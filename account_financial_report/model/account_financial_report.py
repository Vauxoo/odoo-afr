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

from openerp.tools.translate import _
from openerp import models, fields, api


class AccountFinancialReport(models.Model):
    _name = "afr"
    _inherit = "afr.abstract"

    name = fields.Char('Name', size=128, required=True)
    account_ids = fields.Many2many(
        'account.account', 'afr_account_rel', 'afr_id', 'account_id',
        'Root accounts', required=True)
    period_ids = fields.Many2many(
        'account.period', 'afr_period_rel', 'afr_id', 'period_id',
        'Periods', help='All periods in the fiscal year if empty')

    @api.multi
    def copy(self, default=None):
        '''Duplicate a record and changes its name to make it unique'''
        default = dict(default or {})
        new_name = _('Copy of %s') % self.name
        lst = self.search([('name', 'like', new_name)])
        if lst:
            new_name = u'%s (%s)' % (new_name, len(lst) + 1)
        default['name'] = new_name
        return super(AccountFinancialReport, self).copy(default=default)

    @api.onchange('inf_type')
    def onchange_inf_type(self):
        '''When report type changes boolean field analytic ledger changes
        if applies'''
        for brw in self:
            if brw.inf_type != 'BS':
                brw.update({'analytic_ledger': False})

    @api.onchange('columns', 'fiscalyear_id')
    def onchange_columns(self):
        for brw in self:
            values = {}
            if brw.columns != 'four':
                values.update({'analytic_ledger': False})

            values.update({'period_ids': [(6, False, {})]})

            brw.update(values)

    def onchange_analytic_ledger(
            self, cr, uid, ids, company_id, analytic_ledger, context=None):
        context = context and dict(context) or {}
        context['company_id'] = company_id
        res = {'value': {}}
        cur_id = self.pool.get('res.company').browse(
            cr, uid, company_id, context=context).currency_id.id
        res['value'].update({'currency_id': cur_id})
        return res

    def onchange_company_id(self, cr, uid, ids, company_id, context=None):
        context = context and dict(context) or {}
        context['company_id'] = company_id
        res = {'value': {}}

        if not company_id:
            return res

        cur_id = self.pool.get('res.company').browse(
            cr, uid, company_id, context=context).currency_id.id
        fy_id = self.pool.get('account.fiscalyear').find(
            cr, uid, context=context)
        res['value'].update({'fiscalyear_id': fy_id})
        res['value'].update({'currency_id': cur_id})
        res['value'].update({'account_ids': []})
        res['value'].update({'period_ids': []})
        return res
