# coding: utf-8
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://openerp.com.ve>).
#    All Rights Reserved
# Credits######################################################
#    Coded by:   Humberto Arocha <hbto@vauxoo.com>
#                Angelica Barrios angelicaisabelb@gmail.com
#               Jordi Esteve <jesteve@zikzakmedia.com>
#               Javier Duran <javieredm@gmail.com>
#    Planified by: Humberto Arocha
#    Finance by: LUBCAN COL S.A.S http://www.lubcancol.com
#    Audited by: Humberto Arocha humberto@openerp.com.ve
#############################################################################
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################

import time
from openerp.report import report_sxw
from openerp.tools.translate import _
from openerp.osv import osv


class AccountBalance(report_sxw.rml_parse):
    _name = 'afr.parser'

    def __init__(self, cr, uid, name, context):
        super(AccountBalance, self).__init__(cr, uid, name, context)
        self.to_currency_id = None
        self.from_currency_id = None
        self.localcontext.update({
            'getattr': getattr,
            'time': time,
            'lines': self.lines,
            'get_informe_text': self.get_informe_text,
            'get_month': self.get_month,
            'exchange_name': self.exchange_name,
            'get_vat_by_country': self.get_vat_by_country,
        })
        self.context = context

    def get_vat_by_country(self, form):
        """ Return the vat of the partner by country."""
        rc_obj = self.pool.get('res.company')
        country_code = rc_obj.browse(
            self.cr, self.uid,
            form['company_id'][0]).partner_id.country_id.code or ''
        string_vat = rc_obj.browse(self.cr, self.uid,
                                   form['company_id'][0]).partner_id.vat or ''
        if string_vat:
            if country_code == 'MX':
                return ['%s' % (string_vat[2:])]
            elif country_code == 'VE':
                return ['- %s-%s-%s' % (string_vat[2:3], string_vat[3:11],
                                        string_vat[11:12])]
            else:
                return [string_vat]
        else:
            return [_('VAT OF COMPANY NOT AVAILABLE')]

    def get_informe_text(self, form):
        """Returns the header text used on the report."""
        afr_id = form['afr_id'] and isinstance(form['afr_id'], (list, tuple)) \
            and form['afr_id'][0] or form['afr_id']
        if afr_id:
            name = self.pool.get('afr').browse(self.cr, self.uid, afr_id).name
        elif form['analytic_ledger'] and form['columns'] == 'four' and \
                form['inf_type'] == 'BS':
            name = _('Analytic Ledger')
        elif form['inf_type'] == 'BS':
            name = _('Balance Sheet')
        elif form['inf_type'] == 'IS':
            name = _('Income Statement')
        return name

    def get_month(self, form):
        """Return day, year and month."""
        if form['filter'] in ['byperiod', 'all']:
            aux = []
            period_obj = self.pool.get('account.period')

            for period in period_obj.browse(self.cr, self.uid,
                                            form['periods']):
                aux.append(period.date_start)
                aux.append(period.date_stop)
            sorted(aux)
            return _('From ') + self.formatLang(aux[0], date=True) + _(' to ')\
                + self.formatLang(aux[-1], date=True)

    def exchange_name(self, form):
        self.from_currency_id = \
            self.get_company_currency(
                form['company_id'] and
                isinstance(form['company_id'], (list, tuple)) and
                form['company_id'][0] or form['company_id'])
        return self.pool.get('res.currency').browse(self.cr, self.uid,
                                                    self.to_currency_id).name

    def exchange(self, from_amount):
        if self.from_currency_id == self.to_currency_id:
            return from_amount
        curr_obj = self.pool.get('res.currency')
        return curr_obj.compute(self.cr, self.uid, self.from_currency_id,
                                self.to_currency_id, from_amount)

    def get_company_currency(self, company_id):
        rc_obj = self.pool.get('res.company')
        return rc_obj.browse(self.cr, self.uid, company_id).currency_id.id

    def get_company_accounts(self, company_id, acc='credit'):
        rc_obj = self.pool.get('res.company')
        if acc == 'credit':
            return [brw.id for brw in
                    rc_obj.browse(self.cr, self.uid,
                                  company_id).credit_account_ids]
        else:
            return [brw.id for brw in
                    rc_obj.browse(self.cr, self.uid,
                                  company_id).debit_account_ids]

    def _get_partner_balance(self, account, init_period, ctx=None):
        res = []
        ctx = ctx or {}
        if account['type'] in ('other', 'liquidity', 'receivable', 'payable'):
            sql_query = """
                SELECT
                    CASE
                        WHEN aml.partner_id IS NOT NULL
                        THEN (SELECT name FROM res_partner
                                WHERE aml.partner_id = id)
                    ELSE 'UNKNOWN'
                        END AS partner_name,
                    CASE
                        WHEN aml.partner_id IS NOT NULL
                       THEN aml.partner_id
                    ELSE 0
                        END AS p_idx,
                    %s,
                    %s,
                    %s,
                    %s
                FROM account_move_line AS aml
                INNER JOIN account_account aa ON aa.id = aml.account_id
                INNER JOIN account_move am ON am.id = aml.move_id
                %s
                GROUP BY p_idx, partner_name
                """

            where_posted = ''
            if ctx.get('state', 'posted') == 'posted':
                where_posted = "AND am.state = 'posted'"

            cur_periods = ', '.join([str(i) for i in ctx['periods']])
            init_periods = ', '.join([str(i) for i in init_period])

            where = """
                WHERE aml.period_id IN (%s)
                    AND aa.id = %s
                    AND aml.state <> 'draft'
                    """ % (init_periods, account['id'])
            query_init = sql_query % ('SUM(aml.debit) AS init_dr',
                                      'SUM(aml.credit) AS init_cr',
                                      '0.0 AS bal_dr',
                                      '0.0 AS bal_cr',
                                      where + where_posted)

            where = """
                WHERE aml.period_id IN (%s)
                    AND aa.id = %s
                    AND aml.state <> 'draft'
                    """ % (cur_periods, account['id'])

            query_bal = sql_query % ('0.0 AS init_dr',
                                     '0.0 AS init_cr',
                                     'SUM(aml.debit) AS bal_dr',
                                     'SUM(aml.credit) AS bal_cr',
                                     where + where_posted)

            query = '''
                SELECT
                    partner_name,
                    p_idx,
                    SUM(init_dr)-SUM(init_cr) AS balanceinit,
                    SUM(bal_dr) AS debit,
                    SUM(bal_cr) AS credit,
                    SUM(init_dr) - SUM(init_cr) + SUM(bal_dr) - SUM(bal_cr)
                        AS balance
                FROM (
                    SELECT
                    *
                    FROM (%s) vinit
                    UNION ALL (%s)
                ) v
                GROUP BY p_idx, partner_name
                ORDER BY partner_name
                ''' % (query_init, query_bal)

            self.cr.execute(query)
            res_dict = self.cr.dictfetchall()
            unknown = False
            for det in res_dict:
                inicial, debit, credit, balance = det['balanceinit'], det[
                    'debit'], det['credit'], det['balance'],
                data = {
                    'partner_name': det['partner_name'],
                    'balanceinit': inicial,
                    'debit': debit,
                    'credit': credit,
                    'balance': balance,
                }
                if not det['p_idx']:
                    unknown = data
                    continue
                res.append(data)
            if unknown:
                res.append(unknown)
        return res

    def _get_analytic_ledger(self, account, ctx=None):
        """Return a dictionary with all ledger of an account."""
        ctx = ctx or {}
        res = []
        aml_obj = self.pool.get('account.move.line')
        if account['type'] in ('other', 'liquidity', 'receivable', 'payable'):
            # TODO: When period is empty fill it with all periods from
            # fiscalyear but the especial period
            periods = ', '.join([str(i) for i in ctx['periods']])
            where = """where aml.period_id in (%s) and aa.id = %s
            and aml.state <> 'draft'""" % (periods, account['id'])
            if ctx.get('state', 'posted') == 'posted':
                where += "AND am.state = 'posted'"
            sql_detalle = """select aml.id as id, aj.name as diario,
                aa.name as descripcion,
                (select name from res_partner where aml.partner_id = id)
                as partner,
                aa.code as cuenta, aa.id as aa_id, aml.name as name,
                aml.ref as ref,
                (select name from res_currency where aml.currency_id = id)
                as currency,
                aml.currency_id as currency_id,
                aml.partner_id as partner_id,
                aml.amount_currency as amount_currency,
                case when aml.debit is null then 0.00 else aml.debit end
                as debit,
                case when aml.credit is null then 0.00 else aml.credit end
                as credit,
                (select code from account_analytic_account
                where  aml.analytic_account_id = id) as analitica,
                aml.date as date, ap.name as periodo,
                am.name as asiento
                from account_move_line aml
                inner join account_journal aj on aj.id = aml.journal_id
                inner join account_account aa on aa.id = aml.account_id
                inner join account_period ap on ap.id = aml.period_id
                inner join account_move am on am.id = aml.move_id """ \
                + where + """ order by date, am.name"""

            self.cr.execute(sql_detalle)
            resultat = self.cr.dictfetchall()
            balance = account['balanceinit']
            company_currency = self.pool.get('res.currency').browse(
                self.cr, self.uid,
                self.get_company_currency(ctx['company_id'])).name
            for det in resultat:
                balance += det['debit'] - det['credit']
                res.append({
                    'aa_id': det['aa_id'],
                    'cuenta': det['cuenta'],
                    'id': det['id'],
                    'aml_brw': aml_obj.browse(self.cr, self.uid, det['id'],
                                              context=ctx),
                    'date': det['date'],
                    'journal': det['diario'],
                    'partner_id': det['partner_id'],
                    'partner': det['partner'],
                    'name': det['name'],
                    'entry': det['asiento'],
                    'ref': det['ref'],
                    'debit': det['debit'],
                    'credit': det['credit'],
                    'analytic': det['analitica'],
                    'period': det['periodo'],
                    'balance': balance,
                    'currency': det['currency'] or company_currency,
                    'currency_id': det['currency_id'],
                    'amount_currency': det['amount_currency'],
                    'amount_company_currency': det['debit'] - det['credit'] if
                    det['currency'] is None else 0.0,
                    'differential': det['debit'] - det['credit']
                    if det['currency'] is not None and not
                    det['amount_currency'] else 0.0,
                })
        return res

    def _get_journal_ledger(self, account, ctx=None):
        res = []
        am_obj = self.pool.get('account.move')
        if account['type'] in ('other', 'liquidity', 'receivable', 'payable'):
            # TODO: When period is empty fill it with all periods from
            # fiscalyear but the especial period
            periods = ', '.join([str(i) for i in ctx['periods']])
            where = \
                """where aml.period_id in (%s) and aa.id = %s
                    and aml.state <> 'draft'""" % (periods, account['id'])
            if ctx.get('state', 'posted') == 'posted':
                where += "AND am.state = 'posted'"
            sql_detalle = """SELECT
                DISTINCT am.id as am_id,
                aj.name as diario,
                am.name as name,
                am.date as date,
                ap.name as periodo
                from account_move_line aml
                inner join account_journal aj on aj.id = aml.journal_id
                inner join account_account aa on aa.id = aml.account_id
                inner join account_period ap on ap.id = aml.period_id
                inner join account_move am on am.id = aml.move_id """ \
                    + where + """ order by date, am.name"""

            self.cr.execute(sql_detalle)
            resultat = self.cr.dictfetchall()
            for det in resultat:
                res.append({
                    'am_id': det['am_id'],
                    'journal': det['diario'],
                    'name': det['name'],
                    'date': det['date'],
                    'period': det['periodo'],
                    'obj': am_obj.browse(self.cr, self.uid, det['am_id'])
                })
        return res

    def _get_children_and_consol(
            self, cr, uid, ids, level, context=None, change_sign=False):
        """Consolidating Accounts to display them later properly in report."""

        aa_obj = self.pool.get('account.account')
        ids2 = []
        for aa_brw in aa_obj.browse(cr, uid, ids, context):
            if aa_brw.child_id and aa_brw.level < \
                    level and aa_brw.type != 'consolidation':
                if not change_sign:
                    ids2.append([aa_brw.id, True, False, aa_brw])
                ids2.extend(self._get_children_and_consol(
                    cr, uid, [x.id for x in aa_brw.child_id], level,
                    context, change_sign=change_sign))
                if change_sign:
                    ids2.append(aa_brw.id)
                else:
                    ids2.append([aa_brw.id, False, True, aa_brw])
            else:
                if change_sign:
                    ids2.append(aa_brw.id)
                else:
                    ids2.append([aa_brw.id, True, True, aa_brw])
        return ids2

    def _ctx_end(self, ctx, fy_id, form):
        """Context for ending balance"""
        ctx_end = ctx
        ctx_end['filter'] = form.get('filter', 'all')
        ctx_end['fiscalyear_id'] = fy_id.id

        if form['filter'] in ['byperiod', 'all']:
            ctx_end['periods'] = self.pool.get('account.period').search(
                self.cr, self.uid,
                [('id', 'in', form['periods'] or
                  ctx_end.get('periods', False)),
                 ('special', '=', False)])

        return ctx_end.copy()

        #######################################################################
        # CONTEXT FOR INITIAL BALANCE                                         #
        #######################################################################

    def _ctx_init(self, ctx_init, fy_id, form):
        """Context for initial balance"""
        period_obj = self.pool.get('account.period')
        ctx_init['filter'] = form.get('filter', 'all')
        ctx_init['fiscalyear_id'] = fy_id.id

        if form['filter'] in ['byperiod', 'all']:
            ctx_init['periods'] = form['periods']
            date_start = min(
                [period.date_start
                 for period in period_obj.browse(
                     self.cr, self.uid, ctx_init['periods'])])
            ctx_init['periods'] = period_obj.search(
                self.cr, self.uid, [
                    ('fiscalyear_id', '=', fy_id.id),
                    ('date_stop', '<=', date_start)])
        return ctx_init.copy()

    def zfunc(self, nval):
        """Method to return a meaningful value"""
        # TODO: To replace with openerp is_zero method
        return abs(nval) < 0.005 and 0.0 or nval

    def _getting_accounts(self, form):
        """Crunching accounts to easy later computation on accounts"""
        account_obj = self.pool.get('account.account')
        account_ids = form.get('account_list', [])

        credit_account_ids = self.get_company_accounts(
            form.get('company_id') and form['company_id'][0], 'credit')

        debit_account_ids = self.get_company_accounts(
            form.get('company_id') and form['company_id'][0], 'debit')

        ################################################################
        # Get the accounts                                             #
        ################################################################
        all_account_ids = self._get_children_and_consol(
            self.cr, self.uid, account_ids, 100, self.context)

        account_ids = self._get_children_and_consol(
            self.cr, self.uid, account_ids,
            form['display_account_level'] and
            form['display_account_level'] or 100, self.context)

        credit_account_ids = self._get_children_and_consol(
            self.cr, self.uid, credit_account_ids, 100, self.context,
            change_sign=True)

        debit_account_ids = self._get_children_and_consol(
            self.cr, self.uid, debit_account_ids, 100, self.context,
            change_sign=True)

        credit_account_ids = list(set(
            credit_account_ids) - set(debit_account_ids))

        account_black_ids = account_obj.search(
            self.cr, self.uid,
            ([('id', 'in', [i[0] for i in all_account_ids]),
              ('type', 'not in', ('view', 'consolidation'))]))

        account_not_black_ids = account_obj.search(
            self.cr, self.uid,
            ([('id', 'in', [i[0] for i in all_account_ids]),
              ('type', '=', 'view')]))

        acc_cons_ids = account_obj.search(
            self.cr, self.uid,
            ([('id', 'in', [i[0] for i in all_account_ids]),
              ('type', 'in', ('consolidation',))]))

        account_consol_ids = acc_cons_ids and \
            account_obj._get_children_and_consol(
                self.cr, self.uid, acc_cons_ids) or []

        account_black_ids += account_obj.search(
            self.cr, self.uid,
            ([('id', 'in', account_consol_ids),
              ('type', 'not in', ('view', 'consolidation'))]))

        account_black_ids = list(set(account_black_ids))

        c_account_not_black_ids = account_obj.search(
            self.cr, self.uid,
            ([('id', 'in', account_consol_ids), ('type', '=', 'view')]))
        delete_cons = False
        if c_account_not_black_ids:
            delete_cons = set(account_not_black_ids) & set(
                c_account_not_black_ids) and True or False
            account_not_black_ids = list(
                set(account_not_black_ids) - set(c_account_not_black_ids))

        # This could be done quickly with a sql sentence
        account_not_black = account_obj.browse(
            self.cr, self.uid, account_not_black_ids)
        account_not_black.sorted(key=lambda x: x.level, reverse=True)
        account_not_black_ids = [i.id for i in account_not_black]

        c_account_not_black = account_obj.browse(
            self.cr, self.uid, c_account_not_black_ids)
        c_account_not_black.sorted(key=lambda x: x.level, reverse=True)
        c_account_not_black_ids = [i.id for i in c_account_not_black]

        if delete_cons:
            account_not_black_ids = c_account_not_black_ids + \
                account_not_black_ids
            account_not_black = c_account_not_black + account_not_black
        else:
            acc_cons_brw = account_obj.browse(
                self.cr, self.uid, acc_cons_ids)
            acc_cons_brw.sorted(key=lambda x: x.level, reverse=True)
            acc_cons_ids = [i.id for i in acc_cons_brw]

            account_not_black_ids = c_account_not_black_ids + \
                acc_cons_ids + account_not_black_ids
            account_not_black = c_account_not_black + \
                acc_cons_brw + account_not_black

        return (delete_cons, account_black_ids, account_not_black_ids,
                account_not_black, credit_account_ids, account_ids)

    def _process_period(self, form, fy_id):
        period_obj = self.pool.get('account.period')
        ctx_end = {}
        period_ids = []
        pval = []

        if form['columns'] == 'qtr':
            period_ids = period_obj.search(
                self.cr, self.uid,
                [('fiscalyear_id', '=', fy_id.id),
                 ('special', '=', False)],
                order='date_start asc')
            aval = 0
            lval = []
            for xval in period_ids:
                aval += 1
                if aval < 3:
                    lval.append(xval)
                else:
                    lval.append(xval)
                    pval.append(lval)
                    lval = []
                    aval = 0
        elif form['columns'] == 'thirteen':
            period_ids = period_obj.search(
                self.cr, self.uid, [('fiscalyear_id', '=', fy_id.id),
                                    ('special', '=', False)],
                order='date_start asc')
        else:
            ctx_end = self._ctx_end(self.context.copy(), fy_id, form)

        return (ctx_end, period_ids, pval)

    def test_include(self, cols, res, period=None):
        """Check whether lines for certain columns are filled with values."""
        to_test = [False]
        for col in cols:
            if period is None:
                to_test.append(
                    abs(res.get(col, 0.0)) >= 0.005 and True or False)
                continue
            for xval in range(period):
                to_test.append(
                    abs(res.get(col % (xval + 1), 0.0)) >= 0.005 and
                    True or False)
        return any(to_test)

    def check_accounts_to_display(self, form, aa_id, res, period):
        """Check whether we must include this line in the report or not."""
        # Include all accounts unless stated otherwise
        to_include = True
        cols = []

        if form['columns'] in ('thirteen', 'qtr'):
            if form['display_account'] == 'mov' and aa_id[3].parent_id:
                # Include accounts with movements
                cols = ['dbr%s', 'cdr%s']
            elif form['display_account'] == 'bal' and aa_id[3].parent_id:
                # Include accounts with balance
                cols = ['bal%s']
            elif form['display_account'] == 'bal_mov' and aa_id[3].parent_id:
                # Include accounts with balance or movements
                cols = ['dbr%s', 'cdr%s', 'bal%s']
        else:
            if form['display_account'] == 'mov' and aa_id[3].parent_id:
                # Include accounts with movements
                cols = ['debit', 'credit']
            elif form['display_account'] == 'bal' and aa_id[3].parent_id:
                # Include accounts with balance
                cols = ['balance']
            elif form['display_account'] == 'bal_mov' and aa_id[3].parent_id:
                # Include accounts with balance or movements
                cols = ['debit', 'credit', 'balance']
        if cols:
            to_include = self.test_include(cols, res, period)
        return to_include

    def include_ledger(self, res, form, to_include, ctx_i, ctx_end):
        """Includes a Ledger to an account."""
        # ANALYTIC LEDGER
        if (to_include and form['analytic_ledger'] and
                form['columns'] == 'four' and
                form['inf_type'] == 'BS' and
                res['type'] in ('other', 'liquidity', 'receivable',
                                'payable')):
            ctx_end.update(
                company_id=form['company_id'][0],
                report=form['columns'])
            res['mayor'] = self._get_analytic_ledger(res, ctx=ctx_end)
        # JOURNAL LEDGER
        elif to_include and form['journal_ledger'] and \
                form['columns'] == 'four' and form['inf_type'] == 'BS'\
                and res['type'] in ('other', 'liquidity', 'receivable',
                                    'payable'):
            res['journal'] = self._get_journal_ledger(res, ctx=ctx_end)
        # PARTNER LEDGER
        elif to_include and form['partner_balance'] and \
                form['columns'] == 'four' and form['inf_type'] == 'BS'\
                and res['type'] in ('other', 'liquidity', 'receivable',
                                    'payable'):
            res['partner'] = self._get_partner_balance(
                res, ctx_i['periods'], ctx=ctx_end)
        # /!\ NOTE: Is it needed?
        else:
            res['mayor'] = []
        return res

    def get_line_values(self, idx, res, form, all_ap):
        """Fill line with proper values according to report type
        by modifying previously existing dictionary with values."""
        if form['columns'] == 'qtr':
            for pn in range(1, 5):

                if form['inf_type'] == 'IS':
                    debit, credit, balance = [self.zfunc(x) for x in (
                        all_ap[pn - 1][idx].get('debit', 0.0),
                        all_ap[pn - 1][idx].get('credit', 0.0),
                        all_ap[pn - 1][idx].get('balance', 0.0))]
                    res.update({
                        'dbr%s' % pn: self.exchange(debit),
                        'cdr%s' % pn: self.exchange(credit),
                        'bal%s' % pn: self.exchange(balance),
                    })
                else:
                    i, debit, credit = [self.zfunc(x) for x in (
                        all_ap[pn - 1][idx].get('balanceinit', 0.0),
                        all_ap[pn - 1][idx].get('debit', 0.0),
                        all_ap[pn - 1][idx].get('credit', 0.0))]
                    balance = self.zfunc(i + debit - credit)
                    res.update({
                        'dbr%s' % pn: self.exchange(debit),
                        'cdr%s' % pn: self.exchange(credit),
                        'bal%s' % pn: self.exchange(balance),
                    })

            if form['inf_type'] == 'IS':
                debit, credit, balance = [self.zfunc(x) for x in (
                    all_ap['all'][idx].get('debit', 0.0),
                    all_ap['all'][idx].get('credit', 0.0),
                    all_ap['all'][idx].get('balance', 0.0))]
                res.update({
                    'dbr5': self.exchange(debit),
                    'cdr5': self.exchange(credit),
                    'bal5': self.exchange(balance),
                })
            else:
                i, debit, credit = [self.zfunc(x) for x in (
                    all_ap['all'][idx].get('balanceinit', 0.0),
                    all_ap['all'][idx].get('debit', 0.0),
                    all_ap['all'][idx].get('credit', 0.0))]
                balance = self.zfunc(i + debit - credit)
                res.update({
                    'dbr5': self.exchange(debit),
                    'cdr5': self.exchange(credit),
                    'bal5': self.exchange(balance),
                })

        elif form['columns'] == 'thirteen':
            pn = 1
            for p_num in range(12):

                if form['inf_type'] == 'IS':
                    debit, credit, balance = [self.zfunc(x) for x in (
                        all_ap[p_num][idx].get('debit', 0.0),
                        all_ap[p_num][idx].get('credit', 0.0),
                        all_ap[p_num][idx].get('balance', 0.0))]
                    res.update({
                        'dbr%s' % pn: self.exchange(debit),
                        'cdr%s' % pn: self.exchange(credit),
                        'bal%s' % pn: self.exchange(balance),
                    })
                else:
                    i, debit, credit = [self.zfunc(x) for x in (
                        all_ap[p_num][idx].get('balanceinit', 0.0),
                        all_ap[p_num][idx].get('debit', 0.0),
                        all_ap[p_num][idx].get('credit', 0.0))]
                    balance = self.zfunc(i + debit - credit)
                    res.update({
                        'dbr%s' % pn: self.exchange(debit),
                        'cdr%s' % pn: self.exchange(credit),
                        'bal%s' % pn: self.exchange(balance),
                    })

                pn += 1

            if form['inf_type'] == 'IS':
                debit, credit, balance = [self.zfunc(x) for x in (
                    all_ap['all'][idx].get('debit', 0.0),
                    all_ap['all'][idx].get('credit', 0.0),
                    all_ap['all'][idx].get('balance', 0.0))]
                res.update({
                    'dbr13': self.exchange(debit),
                    'cdr13': self.exchange(credit),
                    'bal13': self.exchange(balance),
                })
            else:
                i, debit, credit = [self.zfunc(x) for x in (
                    all_ap['all'][idx].get('balanceinit', 0.0),
                    all_ap['all'][idx].get('debit', 0.0),
                    all_ap['all'][idx].get('credit', 0.0))]
                balance = self.zfunc(i + debit - credit)
                res.update({
                    'dbr13': self.exchange(debit),
                    'cdr13': self.exchange(credit),
                    'bal13': self.exchange(balance),
                })

        else:
            i, debit, credit = [self.zfunc(x) for x in (
                all_ap['all'][idx].get('balanceinit', 0.0),
                all_ap['all'][idx].get('debit', 0.0),
                all_ap['all'][idx].get('credit', 0.0))]
            balance = self.zfunc(i + debit - credit)
            res.update({
                'balanceinit': self.exchange(i),
                'debit': self.exchange(debit),
                'credit': self.exchange(credit),
                'ytd': self.exchange(debit - credit),
            })

            if form['inf_type'] == 'IS' and form['columns'] == 'one':
                res.update({
                    'balance': self.exchange(debit - credit),
                })
            else:
                res.update({
                    'balance': self.exchange(balance),
                })
        return None

    def get_limit(self, form):
        """Iteration limit depending on the number of columns."""
        limit = 1
        if form['columns'] == 'thirteen':
            limit = 13
        elif form['columns'] == 'qtr':
            limit = 5
        return limit

    def get_all_accounts_per_period(
            self, delete_cons, form, p_act, limit, all_account, all_ap,
            account_not_black_ids, dict_not_black):
        """Get values for all accounts in asked periods."""

        for acc_id in account_not_black_ids:
            acc_childs = dict_not_black[acc_id]['obj'].type == 'view' \
                and dict_not_black[acc_id]['obj'].child_id \
                or dict_not_black[acc_id]['obj'].child_consol_ids
            for child_id in acc_childs:
                if child_id.type == 'consolidation' and delete_cons:
                    continue
                if not all_account.get(child_id.id):
                    continue
                dict_not_black[acc_id]['debit'] += \
                    all_account[child_id.id].get('debit')
                dict_not_black[acc_id]['credit'] += \
                    all_account[child_id.id].get('credit')
                dict_not_black[acc_id]['balance'] += \
                    all_account[child_id.id].get('balance')
                if form['inf_type'] == 'BS':
                    dict_not_black[acc_id]['balanceinit'] += \
                        all_account[child_id.id].get('balanceinit')
            all_account[acc_id] = dict_not_black[acc_id]

        if p_act == limit - 1:
            all_ap['all'] = all_account
        else:
            if form['columns'] == 'thirteen':
                all_ap[p_act] = all_account
            elif form['columns'] == 'qtr':
                all_ap[p_act] = all_account
        return None

    def lines(self, form, level=0):
        """Returns all the data needed for the report lines (account info plus
        debit/credit/balance in the selected period and the full year)."""

        account_obj = self.pool.get('account.account')
        fiscalyear_obj = self.pool.get('account.fiscalyear')

        self.context = dict(self.context)
        self.context['state'] = form['target_move'] or 'posted'

        self.from_currency_id = self.get_company_currency(
            form['company_id'] and
            isinstance(form['company_id'], (list, tuple)) and
            form['company_id'][0] or form['company_id'])
        self.to_currency_id = form['currency_id'] and \
            isinstance(form['currency_id'], (list, tuple)) and \
            form['currency_id'][0] or form['currency_id']

        fy_id = form.get('fiscalyear_id') and form['fiscalyear_id'][0]
        fy_id = fiscalyear_obj.browse(self.cr, self.uid, fy_id)

        #
        # Generate the report lines (checking each account)
        #
        tot_bal1 = tot_bal2 = tot_bal3 = tot_bal4 = tot_bal5 = tot_bal6 = 0.0
        tot_bal7 = tot_bal8 = tot_bal9 = tot_bal10 = tot_bal11 = 0.0
        tot_bal12 = tot_bal13 = tot_bin = tot_deb = tot_crd = 0.0
        tot_ytd = tot_eje = 0.0

        res = {}
        tot = {}

        res_process_period = self._process_period(form, fy_id)
        ctx_end = res_process_period[0]
        period_ids = res_process_period[1]
        pval = res_process_period[2]

        ###############################################################
        # Calculations of credit, debit and balance,
        # without repeating operations.
        ###############################################################

        res_getting_accounts = self._getting_accounts(form)
        delete_cons = res_getting_accounts[0]
        account_black_ids = res_getting_accounts[1]
        account_not_black_ids = res_getting_accounts[2]
        account_not_black = res_getting_accounts[3]
        credit_account_ids = res_getting_accounts[4]
        account_ids = res_getting_accounts[5]

        # All accounts per period
        all_ap = {}
        ctx_i = {}

        # Iteration limit depending on the number of columns
        limit = self.get_limit(form)

        for p_act in range(limit):
            if limit != 1:
                if p_act == limit - 1:
                    form['periods'] = period_ids
                else:
                    if form['columns'] == 'thirteen':
                        form['periods'] = [period_ids[p_act]]
                    elif form['columns'] == 'qtr':
                        form['periods'] = pval[p_act]

            ctx_to_use = self._ctx_end(
                self.context.copy(), fy_id, form)

            account_black = account_obj.browse(
                self.cr, self.uid, account_black_ids, ctx_to_use)

            if form['inf_type'] == 'BS':
                ctx_i = self._ctx_init(self.context.copy(), fy_id, form)
                account_black_init = account_obj.browse(
                    self.cr, self.uid, account_black_ids, ctx_i)

            # Black
            dict_black = {}
            for i in account_black:
                debit = i.debit
                credit = i.credit
                dict_black[i.id] = {
                    'obj': i,
                    'debit': debit,
                    'credit': credit,
                    'balance': debit - credit
                }
                if form['inf_type'] == 'BS':
                    dict_black[i.id]['balanceinit'] = 0.0

            # If the report is a balance sheet
            # Balanceinit values are added to the dictionary
            if form['inf_type'] == 'BS':
                for i in account_black_init:
                    dict_black[i.id]['balanceinit'] = i.balance

            # Not black
            dict_not_black = {}
            for i in account_not_black:
                dict_not_black[i.id] = {
                    'obj': i, 'debit': 0.0, 'credit': 0.0, 'balance': 0.0}
                if form['inf_type'] == 'BS':
                    dict_not_black[i.id]['balanceinit'] = 0.0

            # It makes a copy because they modify
            all_account = dict_black.copy()
            self.get_all_accounts_per_period(
                delete_cons, form, p_act, limit, all_account, all_ap,
                account_not_black_ids, dict_not_black)

        ###############################################################
        # End of the calculations of credit, debit and balance
        #
        ###############################################################

        return self._compute_line(
            account_ids, delete_cons, form, tot_bal1, tot_bal2, tot_bal3,
            tot_bal4, tot_bal5, tot_bal6, tot_bal7, tot_bal8, tot_bal9,
            tot_bal10, tot_bal11, tot_bal12, tot_bal13, tot_bin, tot_deb,
            tot_crd, tot_ytd, tot_eje, ctx_i, ctx_end, res, tot, all_ap,
            credit_account_ids)

    def _compute_line(
            self, account_ids, delete_cons, form, tot_bal1, tot_bal2, tot_bal3,
            tot_bal4, tot_bal5, tot_bal6, tot_bal7, tot_bal8, tot_bal9,
            tot_bal10, tot_bal11, tot_bal12, tot_bal13, tot_bin, tot_deb,
            tot_crd, tot_ytd, tot_eje, ctx_i, ctx_end, res, tot, all_ap,
            credit_account_ids):
        """End of the calculations of credit, debit and balance."""

        account_list = form.get('account_list', [])
        tot_check = False
        result_acc = []

        for aa_id in account_ids:
            idx = aa_id[0]
            to_consolidate = aa_id[3].type == 'consolidation' and delete_cons
            #
            # Check if we need to include this level
            #

            to_display = not (not form['display_account_level'] or
                              aa_id[3].level <= form['display_account_level'])
            if any([to_display, to_consolidate]):
                continue

            res = {
                'id': idx,
                'type': aa_id[3].type,
                'code': aa_id[3].code,
                'name': (aa_id[2] and not aa_id[1]) and 'TOTAL %s' %
                (aa_id[3].name.upper()) or aa_id[3].name,
                'parent_id': aa_id[3].parent_id and aa_id[3].parent_id.id,
                'level': aa_id[3].level,
                'label': aa_id[1],
                'total': aa_id[2],
                'change_sign': credit_account_ids and
                (idx in credit_account_ids and -1 or 1) or 1
            }

            self.get_line_values(idx, res, form, all_ap)

            if form['columns'] == 'qtr':
                pn = 5
            elif form['columns'] == 'thirteen':
                pn = 13
            else:
                pn = None

            #
            # Check whether we must include this line in the report or not
            #
            to_include = self.check_accounts_to_display(form, aa_id, res, pn)

            #
            # Include a ledger to the account
            #
            res = self.include_ledger(
                res.copy(), form, to_include, ctx_i, ctx_end)

            if to_include:
                result_acc.append(res)
                #
                # Check whether we must sumarize this line in the report or
                # not
                #
                if form['tot_check'] and (res['id'] in account_list) and \
                        (res['id'] not in tot):
                    if form['columns'] == 'qtr':
                        tot_check = True
                        tot[res['id']] = True
                        tot_bal1 += res.get('bal1', 0.0)
                        tot_bal2 += res.get('bal2', 0.0)
                        tot_bal3 += res.get('bal3', 0.0)
                        tot_bal4 += res.get('bal4', 0.0)
                        tot_bal5 += res.get('bal5', 0.0)

                    elif form['columns'] == 'thirteen':
                        tot_check = True
                        tot[res['id']] = True
                        tot_bal1 += res.get('bal1', 0.0)
                        tot_bal2 += res.get('bal2', 0.0)
                        tot_bal3 += res.get('bal3', 0.0)
                        tot_bal4 += res.get('bal4', 0.0)
                        tot_bal5 += res.get('bal5', 0.0)
                        tot_bal6 += res.get('bal6', 0.0)
                        tot_bal7 += res.get('bal7', 0.0)
                        tot_bal8 += res.get('bal8', 0.0)
                        tot_bal9 += res.get('bal9', 0.0)
                        tot_bal10 += res.get('bal10', 0.0)
                        tot_bal11 += res.get('bal11', 0.0)
                        tot_bal12 += res.get('bal12', 0.0)
                        tot_bal13 += res.get('bal13', 0.0)
                    else:
                        tot_check = True
                        tot[res['id']] = True
                        tot_bin += res['balanceinit']
                        tot_deb += res['debit']
                        tot_crd += res['credit']
                        tot_ytd += res['ytd']
                        tot_eje += res['balance']

        if tot_check:
            str_label = form['lab_str']
            res2 = {
                'type': 'view',
                'name': 'TOTAL %s' % (str_label),
                'label': False,
                'total': True,
            }
            if form['columns'] == 'qtr':
                res2.update(
                    dict(
                        bal1=self.zfunc(tot_bal1),
                        bal2=self.zfunc(tot_bal2),
                        bal3=self.zfunc(tot_bal3),
                        bal4=self.zfunc(tot_bal4),
                        bal5=self.zfunc(tot_bal5),))
            elif form['columns'] == 'thirteen':
                res2.update(
                    dict(
                        bal1=self.zfunc(tot_bal1),
                        bal2=self.zfunc(tot_bal2),
                        bal3=self.zfunc(tot_bal3),
                        bal4=self.zfunc(tot_bal4),
                        bal5=self.zfunc(tot_bal5),
                        bal6=self.zfunc(tot_bal6),
                        bal7=self.zfunc(tot_bal7),
                        bal8=self.zfunc(tot_bal8),
                        bal9=self.zfunc(tot_bal9),
                        bal10=self.zfunc(tot_bal10),
                        bal11=self.zfunc(tot_bal11),
                        bal12=self.zfunc(tot_bal12),
                        bal13=self.zfunc(tot_bal13),))

            else:
                res2.update({
                    'balanceinit': tot_bin,
                    'debit': tot_deb,
                    'credit': tot_crd,
                    'ytd': tot_ytd,
                    'balance': tot_eje,
                })

            result_acc.append(res2)
        return result_acc


class ReportAfr1Cols(osv.AbstractModel):

    # _name = `report.` + `report_name`
    # report_name="afr.1cols"
    _name = 'report.afr.1cols'

    # this inheritance will allow to render this particular report
    _inherit = 'report.abstract_report'  # pylint: disable=R7980
    _template = 'account_financial_report.afr_template'
    _wrapped_report_class = AccountBalance


class ReportAfrAnalyticLedger(osv.AbstractModel):

    # _name = `report.` + `report_name`
    # report_name="afr.analytic.ledger"
    _name = 'report.afr.analytic.ledger'

    # this inheritance will allow to render this particular report
    _inherit = 'report.abstract_report'  # pylint: disable=R7980
    _template = 'account_financial_report.afr_template_analytic_ledger'
    _wrapped_report_class = AccountBalance

report_sxw.report_sxw(
    'report.afr.rml.1cols',
    'wizard.report',
    'account_financial_report/report/balance_full.rml',
    parser=AccountBalance,
    header=False)

report_sxw.report_sxw(
    'report.afr.rml.2cols',
    'wizard.report',
    'account_financial_report/report/balance_full_2_cols.rml',
    parser=AccountBalance,
    header=False)

report_sxw.report_sxw(
    'report.afr.rml.4cols',
    'wizard.report',
    'account_financial_report/report/balance_full_4_cols.rml',
    parser=AccountBalance,
    header=False)

report_sxw.report_sxw(
    'report.afr.rml.analytic.ledger',
    'wizard.report',
    'account_financial_report/report/balance_full_4_cols_analytic_ledger.rml',
    parser=AccountBalance,
    header=False)

report_sxw.report_sxw(
    'report.afr.rml.multicurrency',
    'wizard.report',
    'account_financial_report/report/balance_multicurrency.rml',
    parser=AccountBalance,
    header=False)

report_sxw.report_sxw(
    'report.afr.rml.partner.balance',
    'wizard.report',
    'account_financial_report/report/balance_full_4_cols_partner_balance.rml',
    parser=AccountBalance,
    header=False)

report_sxw.report_sxw(
    'report.afr.rml.journal.ledger',
    'wizard.report',
    'account_financial_report/report/balance_full_4_cols_journal_ledger.rml',
    parser=AccountBalance,
    header=False)

report_sxw.report_sxw(
    'report.afr.rml.5cols',
    'wizard.report',
    'account_financial_report/report/balance_full_5_cols.rml',
    parser=AccountBalance,
    header=False)

report_sxw.report_sxw(
    'report.afr.rml.qtrcols',
    'wizard.report',
    'account_financial_report/report/balance_full_qtr_cols.rml',
    parser=AccountBalance,
    header=False)

report_sxw.report_sxw(
    'report.afr.rml.13cols',
    'wizard.report',
    'account_financial_report/report/balance_full_13_cols.rml',
    parser=AccountBalance,
    header=False)


class ReportAfrPartnerBalance(osv.AbstractModel):

    # _name = `report.` + `report_name`
    # report_name="afr.partner.balance"
    _name = 'report.afr.partner.balance'

    # this inheritance will allow to render this particular report
    _inherit = 'report.abstract_report'  # pylint: disable=R7980
    _template = 'account_financial_report.afr_template_partner_balance'
    _wrapped_report_class = AccountBalance


class ReportAfrJournalLedger(osv.AbstractModel):

    # _name = `report.` + `report_name`
    # report_name="afr.journal.ledger"
    _name = 'report.afr.journal.ledger'

    # this inheritance will allow to render this particular report
    _inherit = 'report.abstract_report'  # pylint: disable=R7980
    _template = 'account_financial_report.afr_template_journal_ledger'
    _wrapped_report_class = AccountBalance


class ReportAfr13Cols(osv.AbstractModel):

    # _name = `report.` + `report_name`
    # report_name="afr.13cols'"
    _name = 'report.afr.13cols'

    # this inheritance will allow to render this particular report
    _inherit = 'report.abstract_report'  # pylint: disable=R7980
    _template = 'account_financial_report.afr_template'
    _wrapped_report_class = AccountBalance
