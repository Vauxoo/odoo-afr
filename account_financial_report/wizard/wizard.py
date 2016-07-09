# coding: utf-8
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://openerp.com.ve>).
#    All Rights Reserved
# Credits######################################################
#    Coded by:   Humberto Arocha humberto@openerp.com.ve
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

from openerp import models, fields, api
from openerp.exceptions import except_orm
from openerp import pooler
from openerp.tools.translate import _


class WizardReport(models.TransientModel):
    _name = "wizard.report"
    _inherit = "afr.abstract"
    _rec_name = 'afr_id'

    afr_id = fields.Many2one(
        'afr', 'Custom Report',
        help='If you have already set a Custom Report, Select it Here.')
    account_list = fields.Many2many(
        'account.account', 'rel_wizard_account', 'account_list',
        'account_id', 'Root accounts', required=True)
    fiscalyear = fields.Many2one(
        'account.fiscalyear', 'Fiscal year',
        help='Fiscal Year for this report', required=True)
    periods = fields.Many2many(
        'account.period', 'rel_wizard_period', 'wizard_id', 'period_id',
        'Periods', help='All periods in the fiscal year if empty')
    group_by = fields.Selection(
        [('currency', 'Currency'), ('partner', 'Partner')],
        'Group by',
        help='Only applies in the way of the end'
        ' balance multicurrency report is show.')

    @api.onchange('company_id')
    def onchange_company_id(self):
        """When `company_id` changes `currency_id`, `fiscalyear_id`,
        `account_list` & `period` fields are filled with Company's Currency,
        Current Fiscal Year, Accounts & Periods are set to blank"""
        for brw in self:
            values = {}
            values.update({'afr_id': None})
            values.update({'account_list': [(6, False, {})]})
            values.update({'periods': [(6, False, {})]})
            brw.update(values)
        return super(WizardReport, self).onchange_company_id()

    def onchange_afr_id(self, cr, uid, ids, afr_id, context=None):
        context = context and dict(context) or {}
        res = {'value': {}}
        if not afr_id:
            return res
        afr_brw = self.pool.get('afr').browse(cr, uid, afr_id, context=context)
        res['value'].update({'currency_id': afr_brw.currency_id and
                             afr_brw.currency_id.id or
                             afr_brw.company_id.currency_id.id})
        res['value'].update({'inf_type': afr_brw.inf_type or 'BS'})
        res['value'].update({'columns': afr_brw.columns or 'five'})
        res['value'].update({'display_account': afr_brw.display_account or
                             'bal_mov'})
        res['value'].update({'display_account_level':
                             afr_brw.display_account_level or 0})
        res['value'].update({'fiscalyear': afr_brw.fiscalyear_id and
                             afr_brw.fiscalyear_id.id})
        res['value'].update({'account_list': [
                            acc.id for acc in afr_brw.account_ids]})
        res['value'].update({'periods': [p.id for p in afr_brw.period_ids]})
        res['value'].update({'analytic_ledger': (afr_brw.analytic_ledger or
                                                 False)})
        res['value'].update({'tot_check': afr_brw.tot_check or False})
        res['value'].update({'lab_str': afr_brw.lab_str or _(
            'Write a Description for your Summary Total')})
        res['value'].update({'report_format': afr_brw.report_format or False})
        res['value'].update(
            {'partner_balance': afr_brw.partner_balance or False})
        res['value'].update(
            {'print_analytic_lines': afr_brw.print_analytic_lines or False})
        return res

    def _get_defaults(self, cr, uid, data, context=None):
        context = context and dict(context) or {}
        user = pooler.get_pool(cr.dbname).get(
            'res.users').browse(cr, uid, uid, context=context)
        if user.company_id:
            company_id = user.company_id.id
        else:
            company_id = pooler.get_pool(cr.dbname).get(
                'res.company').search(cr, uid, [('parent_id', '=', False)])[0]
        data['form']['company_id'] = company_id
        fiscalyear_obj = pooler.get_pool(cr.dbname).get('account.fiscalyear')
        data['form']['fiscalyear'] = fiscalyear_obj.find(cr, uid)
        data['form']['context'] = context
        return data['form']

    def _check_state(self, cr, uid, data, context=None):
        context = context and dict(context) or {}
        if data['form']['filter'] == 'bydate':
            self._check_date(cr, uid, data, context)
        return data['form']

    def _check_date(self, cr, uid, data, context=None):
        context = context and dict(context) or {}

        if data['form']['date_from'] > data['form']['date_to']:
            raise except_orm(_('Error !'), _(
                'La fecha final debe ser mayor a la inicial'))

        sql = """SELECT f.id, f.date_start, f.date_stop
            FROM account_fiscalyear f
            WHERE '%s' = f.id """ % (data['form']['fiscalyear'])
        cr.execute(sql)
        res = cr.dictfetchall()

        if res:
            if (data['form']['date_to'] > res[0]['date_stop'] or
                    data['form']['date_from'] < res[0]['date_start']):
                raise except_orm(_('UserError'),
                                 _('Dates shall be between %s and %s') % (
                    res[0]['date_start'], res[0]['date_stop']))
            else:
                return 'report'
        else:
            raise except_orm(_('UserError'), _('No existe periodo fiscal'))

    def period_span(self, cr, uid, ids, fy_id, context=None):
        context = context and dict(context) or {}
        ap_obj = self.pool.get('account.period')
        fy_id = fy_id and isinstance(fy_id, (list, tuple)) and fy_id[0] or fy_id  # noqa
        if not ids:
            return ap_obj.search(cr, uid, [('fiscalyear_id', '=', fy_id),
                                           ('special', '=', False)],
                                 order='date_start asc')

        ap_brws = ap_obj.browse(cr, uid, ids, context=context)
        date_start = min([period.date_start for period in ap_brws])
        date_stop = max([period.date_stop for period in ap_brws])

        return ap_obj.search(cr, uid, [('fiscalyear_id', '=', fy_id),
                                       ('special', '=', False),
                                       ('date_start', '>=', date_start),
                                       ('date_stop', '<=', date_stop)],
                             order='date_start asc')

    def print_report(self, cr, uid, ids, data, context=None):
        context = context and dict(context) or {}

        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids[0])

        del data['form']['date_from']
        del data['form']['date_to']

        data['form']['periods'] = self.period_span(
            cr, uid, data['form']['periods'], data['form']['fiscalyear'])

        xls = data['form'].get('report_format') == 'xls'

        if data['form']['columns'] == 'currency':
            name = xls and 'afr.multicurrency' or 'afr.rml.multicurrency'
        elif data['form']['columns'] == 'one':
            name = xls and 'afr.1cols' or 'afr.rml.1cols'
        elif data['form']['columns'] == 'two':
            name = xls and 'afr.1cols' or 'afr.rml.2cols'
        elif data['form']['columns'] == 'four':
            if data['form']['analytic_ledger'] and \
                    data['form']['inf_type'] == 'BS':
                name = (xls and 'afr.analytic.ledger' or
                        'afr.rml.analytic.ledger')
            elif data['form']['journal_ledger'] and \
                    data['form']['inf_type'] == 'BS':
                name = xls and 'afr.journal.ledger' or 'afr.rml.journal.ledger'
            elif data['form']['partner_balance'] and \
                    data['form']['inf_type'] == 'BS':
                name = (xls and 'afr.partner.balance' or
                        'afr.rml.partner.balance')
            else:
                name = xls and 'afr.1cols' or 'afr.rml.4cols'
        elif data['form']['columns'] == 'five':
            name = xls and 'afr.1cols' or 'afr.rml.5cols'
        elif data['form']['columns'] == 'qtr':
            name = xls and 'afr.1cols' or 'afr.rml.qtrcols'
        elif data['form']['columns'] == 'thirteen':
            name = xls and 'afr.13cols' or 'afr.rml.13cols'

        if xls:
            context['xls_report'] = xls

            return self.pool['report'].get_action(
                cr, uid, [], name, data=data,
                context=context)

        return {
            'type': 'ir.actions.report.xml',
            'report_name': name,
            'datas': data,
        }
