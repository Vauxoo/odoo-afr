# coding: utf-8

from openerp.tests.common import TransactionCase
from openerp.addons.account_financial_report.report.parser \
    import AccountBalance
import logging

_logger = logging.getLogger(__name__)

JOURNAL_LEDGER = [
    {'balance': -800.0,
     'balanceinit': -500.0,
     'credit': 300.0,
     'debit': 0.0,
     'journal': [{}]},
]

PARTNER_BALANCE = [
    {'balance': 1200.0,
     'balanceinit': 1000.0,
     'credit': 0.0,
     'debit': 200.0,
     'partner': [
         {'balance': 200.0,
          'balanceinit': 0.0,
          'credit': 0.0,
          'partner_name': 'Vauxoo',
          'debit': 200.0, },
         {'balance': 1000.0,
          'balanceinit': 1000.0,
          'credit': 0.0,
          'partner_name': 'UNKNOWN',
          'debit': 0.0, },
     ]},
    {'balance': -800.0,
     'balanceinit': -800.0,
     'credit': 0.0,
     'debit': 0.0,
     'partner': [
         {'balance': -800.0,
          'balanceinit': -800.0,
          'credit': 0.0,
          'partner_name': 'UNKNOWN',
          'debit': 0.0, }]},
]

ANALYTIC_LEDGER = [
    {'balance': 1000.0,
     'balanceinit': 1000.0,
     'credit': 0.0,
     'debit': 0.0,
     'mayor': []},
    {'balance': -800.0,
     'balanceinit': -500.0,
     'credit': 300.0,
     'debit': 0.0,
     'mayor': [
         {'balance': -800.0,
          'credit': 300.0,
          'debit': 0.0, }]},
    {'balance': 300.0,
     'balanceinit': 0.0,
     'credit': 0.0,
     'debit': 300.0,
     'mayor': [
         {'balance': 300.0,
          'credit': 0.0,
          'debit': 300.0, }]}
]

BS_QTR = {
    'bal1': 1000.0,
    'bal2': 1200.0,
    'bal3': 1200.0,
    'bal4': 1200.0,
    'bal5': 1200.0,
    }

IS_QTR = {
    'bal1': 0.0,
    'bal2': 200.0,
    'bal3': 0.0,
    'bal4': 0.0,
    'bal5': 200.0,
    }

BS_13 = {
    'bal1': 1000.0,
    'bal2': 1000.0,
    'bal3': 1000.0,
    'bal4': 1000.0,
    'bal5': 1200.0,
    'bal6': 1200.0,
    'bal7': 1200.0,
    'bal8': 1200.0,
    'bal9': 1200.0,
    'bal10': 1200.0,
    'bal11': 1200.0,
    'bal12': 1200.0,
    'bal13': 1200.0,
    }

IS_13 = {
    'bal1': 0.0,
    'bal2': 0.0,
    'bal3': 0.0,
    'bal4': 0.0,
    'bal5': 200.0,
    'bal6': 0.0,
    'bal7': 0.0,
    'bal8': 0.0,
    'bal9': 0.0,
    'bal10': 0.0,
    'bal11': 0.0,
    'bal12': 0.0,
    'bal13': 200.0,
    }


class TestReportAFR(TransactionCase):

    def setUp(self):
        super(TestReportAFR, self).setUp()
        self.wiz_rep_obj = self.env['wizard.report']

        self.company_id = self.ref('base.main_company')
        self.fiscalyear_id = self.ref('account.data_fiscalyear')
        self.currency_id = self.ref('base.EUR')
        self.account_list = []
        self.a_pay = self.ref('account_financial_report.a_pay')
        self.a_recv = self.ref('account_financial_report.a_recv')
        self.rev = self.ref('account_financial_report.rev')
        self.srv = self.ref('account_financial_report.srv')
        self.account_list += [(4, self.a_pay, 0)]
        self.account_list += [(4, self.a_recv, 0)]
        self.account_list += [(4, self.rev, 0)]
        self.account_list += [(4, self.srv, 0)]
        self.values = {
            'company_id': self.company_id,
            'inf_type': 'BS',
            'columns': 'four',
            'currency_id': self.currency_id,
            'report_format': 'xls',
            'display_account': 'bal_mov',
            'fiscalyear': self.fiscalyear_id,
            'display_account_level': 0,
            'target_move': 'posted',
            'tot_check': False,
            'periods': [],
            'account_list': [],
        }

    def test_lines_report_afr_pay_period_01(self):
        _logger.info('Testing Payables at Period 01')
        account_id = self.ref('account_financial_report.a_pay')
        period_id = self.ref('account.period_1')
        values = dict(
            self.values,
            periods=[(4, period_id, 0)],
            account_list=[(4, account_id, 0)]
        )
        lines = self._generate_afr(values)
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

    def test_lines_report_afr_pay_period_03_is_one_col(self):
        _logger.info('Testing Payables at Period 03 One Column')
        account_id = self.ref('account_financial_report.a_pay')
        period_id = self.ref('account.period_3')
        values = dict(
            self.values,
            columns='one',
            periods=[(4, period_id, 0)],
            account_list=[(4, account_id, 0)],
            inf_type='IS',
        )
        lines = self._generate_afr(values)
        if lines and lines[0]:
            lines = lines[0]
            self.assertEqual(lines.get('id'), account_id, 'Wrong Account')
            self.assertEqual(lines.get('balance'), -300)
            self.assertEqual(lines.get('ytd'), -300)
        else:
            self.assertTrue(False, 'Something went wrong with Test')

    def test_lines_report_afr_pay_period_03(self):
        _logger.info('Testing Payables at Period 03')
        account_id = self.ref('account_financial_report.a_pay')
        period_id = self.ref('account.period_3')
        values = dict(
            self.values,
            periods=[(4, period_id, 0)],
            account_list=[(4, account_id, 0)]
        )
        lines = self._generate_afr(values)
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

    def test_lines_report_partner_balance_period_05(self):
        _logger.info('Testing Partner Balance at Period 05')
        period_id = self.ref('account.period_5')
        values = dict(
            self.values,
            periods=[(4, period_id, 0)],
            account_list=[(4, self.a_recv, 0), (4, self.a_pay, 0)],
            partner_balance=True,
        )
        lines = self._generate_afr(values)

        if not lines:
            self.assertTrue(False, 'Something went wrong with Test')

        self.assertEqual(len(lines), 2, 'There should be 2 Lines')
        zipped = zip(PARTNER_BALANCE, lines)
        for elem in zipped:
            std, res = elem
            for col in std:
                if col != 'partner':
                    self.assertEqual(
                        res.get(col), std[col],
                        'Something went wrong for %s' % col)
                    continue

                self.assertEqual(
                    len(res.get(col)), len(std[col]),
                    'Something went wrong for %s' % col)
                zipped2 = zip(std.get(col), res.get(col))
                for elem2 in zipped2:
                    std2, res2 = elem2
                    for col2 in std2:
                        self.assertEqual(
                            res2.get(col2), std2[col2],
                            'Something went wrong for %s' % col2)

    def test_lines_report_journal_ledger_period_03(self):
        _logger.info('Testing Journal Ledger at Period 03')
        period_id = self.ref('account.period_3')
        values = dict(
            self.values,
            periods=[(4, period_id, 0)],
            account_list=[(4, self.a_pay, 0)],
            journal_ledger=True,
        )
        lines = self._generate_afr(values)

        if not lines:
            self.assertTrue(False, 'Something went wrong with Test')

        self.assertEqual(len(lines), 1, 'There should be 1 Lines')
        zipped = zip(JOURNAL_LEDGER, lines)
        for elem in zipped:
            std, res = elem
            for col in std:
                if col != 'journal':
                    self.assertEqual(
                        res.get(col), std[col],
                        'Something went wrong for %s' % col)
                    continue

                self.assertEqual(
                    len(res.get(col)), len(std[col]),
                    'Something went wrong for %s' % col)
                zipped2 = zip(std.get(col), res.get(col))
                for elem2 in zipped2:
                    std2, res2 = elem2
                    for col2 in std2:
                        self.assertEqual(
                            res2.get(col2), std2[col2],
                            'Something went wrong for %s' % col2)

    def test_lines_report_analytic_ledger_period_03(self):
        _logger.info('Testing Analytic Ledger at Period 03')
        period_id = self.ref('account.period_3')
        values = dict(
            self.values,
            periods=[(4, period_id, 0)],
            account_list=self.account_list,
            analytic_ledger=True,
        )
        lines = self._generate_afr(values)
        if not lines:
            self.assertTrue(False, 'Something went wrong with Test')

        self.assertEqual(len(lines), 3, 'There should be 3 Lines')
        zipped = zip(ANALYTIC_LEDGER, lines)
        for elem in zipped:
            std, res = elem
            for col in std:
                if col == 'mayor':
                    self.assertEqual(
                        len(res.get(col)), len(std[col]),
                        'Something went wrong for %s' % col)
                    zipped2 = zip(std.get(col), res.get(col))
                    for elem2 in zipped2:
                        std2, res2 = elem2
                        for col2 in std2:
                            self.assertEqual(
                                res2.get(col2), std2[col2],
                                'Something went wrong for %s' % col2)
                else:
                    self.assertEqual(
                        res.get(col), std[col],
                        'Something went wrong for %s' % col)

    def test_display_all(self):
        _logger.info('Testing Display All Account at Period 03')
        period_id = self.ref('account.period_3')
        account_list = self.account_list
        values = dict(
            self.values,
            display_account='all',
            periods=[(4, period_id, 0)],
            account_list=account_list,
            tot_check=True,
        )
        lines = self._generate_afr(values)
        if lines and lines[-1]:
            self.assertEqual(len(lines), 5, 'There should be 5 Lines')
            lines = lines[-1]
            self.assertEqual(lines.get('balanceinit'), 500)
            self.assertEqual(lines.get('debit'), 300)
            self.assertEqual(lines.get('credit'), 300)
            self.assertEqual(lines.get('balance'), 500)
            self.assertEqual(lines.get('ytd'), 0)
        else:
            self.assertTrue(False, 'Something went wrong with Test')
        values = dict(
            values,
            display_account='bal_mov',
        )
        lines = self._generate_afr(values)
        if lines and lines[-1]:
            self.assertEqual(len(lines), 4, 'There should be 4 Lines')
            lines = lines[-1]
            self.assertEqual(lines.get('balanceinit'), 500)
            self.assertEqual(lines.get('debit'), 300)
            self.assertEqual(lines.get('credit'), 300)
            self.assertEqual(lines.get('balance'), 500)
            self.assertEqual(lines.get('ytd'), 0)
        else:
            self.assertTrue(False, 'Something went wrong with Test')
        values = dict(
            values,
            display_account='mov',
        )
        lines = self._generate_afr(values)
        if lines and lines[-1]:
            self.assertEqual(len(lines), 3, 'There should be 3 Lines')
            lines = lines[-1]
            self.assertEqual(lines.get('balanceinit'), -500)
            self.assertEqual(lines.get('debit'), 300)
            self.assertEqual(lines.get('credit'), 300)
            self.assertEqual(lines.get('balance'), -500)
            self.assertEqual(lines.get('ytd'), 0)
        else:
            self.assertTrue(False, 'Something went wrong with Test')
        values = dict(
            values,
            display_account='bal',
        )
        lines = self._generate_afr(values)
        if lines and lines[-1]:
            self.assertEqual(len(lines), 4, 'There should be 4 Lines')
            lines = lines[-1]
            self.assertEqual(lines.get('balanceinit'), 500)
            self.assertEqual(lines.get('debit'), 300)
            self.assertEqual(lines.get('credit'), 300)
            self.assertEqual(lines.get('balance'), 500)
            self.assertEqual(lines.get('ytd'), 0)
        else:
            self.assertTrue(False, 'Something went wrong with Test')

    def test_lines_report_afr_pay_period_05(self):
        _logger.info('Testing Payables at Period 05')
        account_id = self.ref('account_financial_report.a_pay')
        period_id = self.ref('account.period_5')
        values = dict(
            self.values,
            periods=[(4, period_id, 0)],
            account_list=[(4, account_id, 0)]
        )
        lines = self._generate_afr(values)
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
        values = dict(
            self.values,
            account_list=[(4, account_id, 0)]
        )
        lines = self._generate_afr(values)
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

    def test_rec_qtr(self):
        _logger.info('Testing Receivables at Quarter Cols')
        account_id = self.ref('account_financial_report.a_recv')
        values = dict(
            self.values,
            columns='qtr',
            inf_type='BS',
            display_account='mov',
            periods=[],
            account_list=[(4, account_id, 0)]
        )
        lines = self._generate_afr(values)
        if lines and lines[0]:
            res = lines[0]
            for col in BS_QTR:
                self.assertEqual(
                    res.get(col), BS_QTR[col],
                    'Something went wrong for %s' % col
                )
        if not lines or lines and not lines[0]:
            self.assertTrue(False, 'Something went wrong with Test')
        values = dict(
            values,
            display_account='bal',
            tot_check=True,
        )
        lines = self._generate_afr(values)
        if lines and lines[0]:
            res = lines[0]
            for col in BS_QTR:
                self.assertEqual(
                    res.get(col), BS_QTR[col],
                    'Something went wrong for %s' % col
                )
        if lines and lines[1]:
            res = lines[1]
            self.assertEqual(res.get('type'), 'view')
            for col in BS_QTR:
                self.assertEqual(
                    res.get(col), BS_QTR[col],
                    'Something went wrong for %s' % col
                )
        if not lines or lines and (not lines[0] or not lines[1]):
            self.assertTrue(False, 'Something went wrong with Test')
        values = dict(
            values,
            tot_check=False,
            display_account='all',
            inf_type='IS',
        )
        lines = self._generate_afr(values)
        if lines and lines[0]:
            res = lines[0]
            for col in IS_QTR:
                self.assertEqual(
                    res.get(col), IS_QTR[col],
                    'Something went wrong for %s' % col
                )
        if not lines or lines and not lines[0]:
            self.assertTrue(False, 'Something went wrong with Test')
        return True

    def test_rec_thirteen(self):
        _logger.info('Testing Receivables at Thirteen Cols')
        account_id = self.ref('account_financial_report.a_recv')
        values = dict(
            self.values,
            columns='thirteen',
            inf_type='BS',
            periods=[],
            account_list=[(4, account_id, 0)]
        )
        lines = self._generate_afr(values)
        if lines and lines[0]:
            res = lines[0]
            for col in BS_13:
                self.assertEqual(
                    res.get(col), BS_13[col],
                    'Something went wrong for %s' % col
                )
        if not lines or lines and not lines[0]:
            self.assertTrue(False, 'Something went wrong with Test')
        values = dict(
            values,
            tot_check=True,
        )
        lines = self._generate_afr(values)
        if lines and lines[0]:
            res = lines[0]
            for col in BS_13:
                self.assertEqual(
                    res.get(col), BS_13[col],
                    'Something went wrong for %s' % col
                )
        if lines and lines[1]:
            res = lines[1]
            self.assertEqual(res.get('type'), 'view')
            for col in BS_13:
                self.assertEqual(
                    res.get(col), BS_13[col],
                    'Something went wrong for %s' % col
                )
        if not lines or lines and (not lines[0] or not lines[1]):
            self.assertTrue(False, 'Something went wrong with Test')
        values = dict(
            values,
            tot_check=False,
            inf_type='IS',
        )
        lines = self._generate_afr(values)
        if lines and lines[0]:
            res = lines[0]
            for col in IS_13:
                self.assertEqual(
                    res.get(col), IS_13[col],
                    'Something went wrong for %s' % col
                )
        if not lines or lines and not lines[0]:
            self.assertTrue(False, 'Something went wrong with Test')
        return True

    def test_rec_period_05_is(self):
        _logger.info('Testing Receivables at Period 05')
        account_id = self.ref('account_financial_report.a_recv')
        period_id = self.ref('account.period_5')
        values = dict(
            self.values,
            inf_type='IS',
            tot_check=True,
            periods=[(4, period_id, 0)],
            account_list=[(4, account_id, 0)]
        )
        lines = self._generate_afr(values)
        if lines and lines[0]:
            res = lines[0]
            self.assertEqual(res.get('type'), 'receivable')
            self.assertEqual(res.get('id'), account_id, 'Wrong Account')
            self.assertEqual(res.get('balanceinit'), 0)
            self.assertEqual(res.get('debit'), 200)
            self.assertEqual(res.get('credit'), 0)
            self.assertEqual(res.get('balance'), 200)
            self.assertEqual(res.get('ytd'), 200)
        if lines and lines[1]:
            res = lines[1]
            self.assertEqual(res.get('type'), 'view')
            self.assertEqual(res.get('balanceinit'), 0)
            self.assertEqual(res.get('debit'), 200)
            self.assertEqual(res.get('credit'), 0)
            self.assertEqual(res.get('balance'), 200)
            self.assertEqual(res.get('ytd'), 200)
        if not lines or lines and (not lines[0] or not lines[1]):
            self.assertTrue(False, 'Something went wrong with Test')
        return True

    def test_get_vat_by_country(self):
        _logger.info('Testing Country VAT')
        account_id = self.ref('account_financial_report.a_recv')
        period_id = self.ref('account.period_5')
        period_id = [(4, period_id, 0)]
        values = dict(
            self.values,
            periods=period_id,
            account_list=[(4, account_id, 0)]
        )
        data = self._get_data(values)
        res = AccountBalance(
            self.cr, self.uid, '', {}).get_vat_by_country(
                data['data']['form'])
        if res and res[0]:
            res = res[0]
            self.assertEqual(res, 'VAT OF COMPANY NOT AVAILABLE')
        else:
            self.assertTrue(False, 'Something went wrong with Test')
        return True

    def test_get_informe_text(self):
        _logger.info('Testing Inform Text')
        account_id = self.ref('account_financial_report.a_recv')
        period_id = self.ref('account.period_5')
        values = dict(
            self.values,
            periods=[(4, period_id, 0)],
            account_list=[(4, account_id, 0)]
        )
        data = self._get_data(values)
        res = AccountBalance(
            self.cr, self.uid, '', {}).get_informe_text(
                data['data']['form'])
        self.assertEqual(res, 'Balance Sheet')
        return True

    def get_month(self):
        _logger.info('Testing Month')
        account_id = self.ref('account_financial_report.a_recv')
        period_id = self.ref('account.period_5')
        values = dict(
            self.values,
            periods=[(4, period_id, 0)],
            account_list=[(4, account_id, 0)]
        )
        data = self._get_data(values)
        res = AccountBalance(
            self.cr, self.uid, '', {}).get_month(
                data['data']['form'])
        self.assertEqual(res, 'From 05/01/2016 to 05/31/2016')
        return True

    def _get_data(self, values):

        wiz_id = self.wiz_rep_obj.create(values)

        context = {
            'xls_report': True,
            'active_model': 'wizard.report',
            'active_ids': [wiz_id.id],
            'active_id': wiz_id.id,
        }
        return wiz_id.with_context(context).print_report({})

    def _generate_afr(self, values):
        data = self._get_data(values)
        return AccountBalance(
            self.cr, self.uid, '', {}).lines(data['data']['form'])
