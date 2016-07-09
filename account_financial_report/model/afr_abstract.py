# coding: utf-8

from openerp import models, fields, api


class AfrAbstract(models.AbstractModel):
    _name = "afr.abstract"

    company_id = fields.Many2one(
        'res.company', 'Company', required=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'ifrs.ifrs'))
    currency_id = fields.Many2one(
        'res.currency', 'Currency',
        help="Currency at which this report will be expressed. If not "
        "selected will be used the one set in the company")
    inf_type = fields.Selection(
        [('BS', 'Ending Balance'),
         ('IS', 'Variation on Periods')],
        'Type', required=True, default='BS')
    columns = fields.Selection(
        [('one', 'End. Balance'),
         ('two', 'Debit | Credit'),
         ('four', 'Initial | Debit | Credit | YTD'),
         ('five', 'Initial | Debit | Credit | Period | YTD'),
         ('qtr', "4 QTR's | YTD"),
         ('thirteen', '12 Months | YTD')],
        'Columns', required=True, default='four')
    display_account = fields.Selection(
        [('all', 'All Accounts'),
         ('bal', 'With Balance'),
         ('mov', 'With movements'),
         ('bal_mov', 'With Balance / Movements')],
        'Display accounts', default='bal_mov')
    display_account_level = fields.Integer(
        'Up to level', default=0,
        help='Display accounts up to this level (0 to show all)')
    account_ids = fields.Many2many(
        'account.account', 'afr_account_rel', 'afr_id', 'account_id',
        'Root accounts', required=True)
    fiscalyear_id = fields.Many2one(
        'account.fiscalyear', 'Fiscal year',
        default=lambda self: self.env['account.fiscalyear'].find(
            exception=False),
        help='Fiscal Year for this report', required=True)
    period_ids = fields.Many2many(
        'account.period', 'afr_period_rel', 'afr_id', 'period_id',
        'Periods', help='All periods in the fiscal year if empty')
    analytic_ledger = fields.Boolean(
        'Analytic Ledger',
        help="Allows to Generate an Analytic Ledger for accounts with "
        "moves. Available when Balance Sheet and 'Initial | Debit | "
        "Credit | YTD' are selected")
    journal_ledger = fields.Boolean(
        'journal Ledger',
        help="Allows to Generate an journal Ledger for accounts with "
        "moves. Available when Balance Sheet and 'Initial | Debit | "
        "Credit | YTD' are selected")
    partner_balance = fields.Boolean(
        'Partner Balance', help="Allows to Generate a Partner Balance for "
        "accounts with moves. Available when Balance Sheet and 'Initial | "
        "Debit | Credit | YTD' are selected")
    tot_check = fields.Boolean(
        'Summarize?',
        help='Checking will add a new line at the end of the Report which '
        'will Summarize Columns in Report')
    lab_str = fields.Char(
        'Description',
        help='Description for the Summary',
        size=128)
    target_move = fields.Selection(
        [('posted', 'All Posted Entries'), ('all', 'All Entries')],
        'Entries to Include', required=True, default='posted',
        help='Print All Accounting Entries or just Posted Accounting '
        'Entries')
    group_by = fields.Selection(
        [('currency', 'Currency'), ('partner', 'Partner')],
        'Group by',
        help='Only applies in the way of the end'
        ' balance multicurrency report is show.')
    lines_detail = fields.Selection(
        [
            ('detail', 'Detail'),
            ('full', 'Full Detail'),
            ('total', 'Totals')],
        'Line Details',
        help='Only applies in the way of the end balance multicurrency'
        ' report is show.')
    print_analytic_lines = fields.Boolean(
        'With Analytic Lines',
        help="If this checkbox is active will print the analytic lines in"
        " the analytic ledger four columns report. This option only"
        " applies when the analytic ledger is selected.")
    report_format = fields.Selection([
        ('pdf', 'PDF'),
        ('xls', 'Spreadsheet')], 'Report Format', default='pdf')

    # Deprecated fields
    filter = fields.Selection(
        [('bydate', 'By Date'), ('byperiod', 'By Period'),
         ('all', 'By Date and Period'), ('none', 'No Filter')],
        'Date/Period Filter', default='byperiod')
    date_to = fields.Date('End date')
    date_from = fields.Date('Start date')

    @api.onchange('inf_type')
    def onchange_inf_type(self):
        """When report type changes boolean field analytic ledger changes
        if applies"""
        for brw in self:
            if brw.inf_type != 'BS':
                brw.update({'analytic_ledger': False})

    @api.onchange('columns', 'fiscalyear_id')
    def onchange_columns(self):
        """When `columns` or `fiscalyear_id` changes `period_ids` field changes
        if applies"""
        for brw in self:
            values = {}
            if brw.columns != 'four':
                values.update({'analytic_ledger': False})

            values.update({'period_ids': [(6, False, {})]})

            brw.update(values)

    @api.onchange('analytic_ledger')
    def onchange_analytic_ledger(self):
        """When `analytic_ledger` changes `currency_id` field changes to
        Company's Currency"""
        for brw in self:
            if brw.analytic_ledger:
                brw.update({'currency_id': self.company_id.currency_id.id})

    @api.onchange('company_id')
    def onchange_company_id(self):
        """When `company_id` changes `currency_id`, `fiscalyear_id`,
        `account_id` & `period_ids` fields are filled with Company's Currency,
        Current Fiscal Year, Accounts & Periods are set to blank"""
        for brw in self:
            values = {}
            values.update({'currency_id': self.company_id.currency_id.id})
            values.update(
                {'fiscalyear_id': self.env['account.fiscalyear'].find()})
            values.update({'account_ids': [(6, False, {})]})
            values.update({'period_ids': [(6, False, {})]})
            brw.update(values)
