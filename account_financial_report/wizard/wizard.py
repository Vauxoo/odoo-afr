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

    @api.onchange('afr_id')
    def onchange_afr_id(self):
        """Takes the fields in the template and fields those on the wizard"""
        for brw in self:
            brw.update({'account_list': [(6, False, {})]})
            brw.update({'periods': [(6, False, {})]})
            if not brw.afr_id:
                continue
            values = brw.afr_id.copy_data()[0]
            values.pop('name')
            # TODO: Change fields
            # `account_list` to `account_ids` and `periods`to `period_ids`
            values.update(
                {'account_list': values['account_ids'][:]})
            values.update(
                {'periods': values['period_ids'][:]})
            values.pop('account_ids')
            values.pop('period_ids')
            brw.update(values)

    @api.multi
    def period_span(self):
        """Method to provide period list into report"""
        args = [('fiscalyear_id', '=', self.fiscalyear_id.id),
                ('special', '=', False)]
        if self.periods:
            date_start = min([period.date_start for period in self.periods])
            date_stop = max([period.date_stop for period in self.periods])
            args.extend([
                ('date_start', '>=', date_start),
                ('date_stop', '<=', date_stop)])

        res = self.periods.with_context(self._context).search(
            args, order='date_start asc')
        return [brw.id for brw in res]

    @api.multi
    def print_report(self):
        """Method to preprocess data and print a report"""
        context = dict(self._context)

        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read()[0]

        del data['form']['date_from']
        del data['form']['date_to']

        data['form']['periods'] = self.period_span()

        xls = data['form'].get('report_format') == 'xls'

        if data['form']['columns'] == 'one':
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

            return self.env['report'].with_context(context).get_action(
                self, name, data=data)

        return {
            'type': 'ir.actions.report.xml',
            'report_name': name,
            'datas': data,
        }
