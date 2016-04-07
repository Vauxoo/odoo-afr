# coding: utf-8

from openerp.tests.common import TransactionCase
from openerp.addons.account_financial_report.report.parser \
    import AccountBalance
import logging

_logger = logging.getLogger(__name__)


class TestReportAFR(TransactionCase):

    def setUp(self):
        super(TestReportAFR, self).setUp()
        self.wiz_rep_obj = self.env['wizard.report']

        self.company_id = self.ref('base.main_company')
        self.fiscalyear_id = self.ref('account.data_fiscalyear')
        self.currency_id = self.ref('base.EUR')

    def test_lines_report_afr_pay_period_01(self):
        _logger.info('Testing Payables at Period 01')
        account_id = self.ref('account_financial_report.a_pay')
        period_id = self.ref('account.period_1')
        lines = self._generate_afr(account_id, [(4, period_id, 0)])
        if lines and lines[0]:
            lines = lines[0]
            self.assertEqual(lines.get('id'), account_id, 'Wrong Account')
            self.assertEqual(lines.get('balanceinit'), -500)
            self.assertEqual(lines.get('debit'), 0)
            self.assertEqual(lines.get('credit'), 0)
            self.assertEqual(lines.get('balance'), -500)
            self.assertEqual(lines.get('ytd'), 0)
        else:
            self.assertTrue(False, 'Something went wrong with Test')

    def test_lines_report_afr_pay_period_03(self):
        _logger.info('Testing Payables at Period 03')
        account_id = self.ref('account_financial_report.a_pay')
        period_id = self.ref('account.period_3')
        lines = self._generate_afr(account_id, [(4, period_id, 0)])
        if lines and lines[0]:
            lines = lines[0]
            self.assertEqual(lines.get('id'), account_id, 'Wrong Account')
            self.assertEqual(lines.get('balanceinit'), -500)
            self.assertEqual(lines.get('debit'), 0)
            self.assertEqual(lines.get('credit'), 300)
            self.assertEqual(lines.get('balance'), -800)
            self.assertEqual(lines.get('ytd'), -300)
        else:
            self.assertTrue(False, 'Something went wrong with Test')

    def test_lines_report_afr_pay_period_05(self):
        _logger.info('Testing Payables at Period 05')
        account_id = self.ref('account_financial_report.a_pay')
        period_id = self.ref('account.period_5')
        lines = self._generate_afr(account_id, [(4, period_id, 0)])
        if lines and lines[0]:
            lines = lines[0]
            self.assertEqual(lines.get('id'), account_id, 'Wrong Account')
            self.assertEqual(lines.get('balanceinit'), -800)
            self.assertEqual(lines.get('debit'), 0)
            self.assertEqual(lines.get('credit'), 0)
            self.assertEqual(lines.get('balance'), -800)
            self.assertEqual(lines.get('ytd'), 0)
        else:
            self.assertTrue(False, 'Something went wrong with Test')

    def test_lines_report_afr_pay_period_all(self):
        _logger.info('Testing Payables All Periods')
        account_id = self.ref('account_financial_report.a_pay')
        lines = self._generate_afr(account_id, [])
        if lines and lines[0]:
            lines = lines[0]
            self.assertEqual(lines.get('id'), account_id, 'Wrong Account')
            self.assertEqual(lines.get('balanceinit'), -500)
            self.assertEqual(lines.get('debit'), 0)
            self.assertEqual(lines.get('credit'), 300)
            self.assertEqual(lines.get('balance'), -800)
            self.assertEqual(lines.get('ytd'), -300)
        else:
            self.assertTrue(False, 'Something went wrong with Test')

    def _generate_afr(self, account_id, period_id, inf_type='BS'):
        wiz_id = self.wiz_rep_obj.create({
            'company_id': self.company_id,
            'inf_type': inf_type,
            'columns': 'four',
            'currency_id': self.currency_id,
            'report_format': 'xls',
            'display_account': 'bal_mov',
            'fiscalyear': self.fiscalyear_id,
            'display_account_level': 0,
            'target_move': 'posted',
            'periods': period_id,
            'account_list': [(4, account_id, 0)]})

        context = {
            'xls_report': True,
            'active_model': 'wizard.report',
            'active_ids': [wiz_id.id],
            'active_id': wiz_id.id,
        }
        data = wiz_id.with_context(context).print_report({})
        return AccountBalance(
            self.cr, self.uid, '', {}).lines(data['data']['form'])
