# coding: utf-8

import logging
import time
from openerp.tests.common import TransactionCase
from ..report.parser import AccountBalance

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
          'partner_name': 'VX',
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
        self.acc_obj = self.registry('account.account')
        self.acc_obj._parent_store_compute(self.cr)

        self.wiz_rep_obj = self.env['wizard.report']
        self.afr_obj = self.env['afr']

        self.company_id = self.ref('base.main_company')
        self.fiscalyear_id = self.ref('account.data_fiscalyear')
        self.currency_id = self.ref('base.EUR')
        self.account_list = []
        self.afr_id = self.ref('account_financial_report.afr_01')
        self.period_1 = self.ref('account.period_1')
        self.period_3 = self.ref('account.period_3')
        self.period_5 = self.ref('account.period_5')
        self.chart0 = self.ref('account.chart0')
        self.a_pay = self.ref('account_financial_report.a_pay')
        self.a_recv = self.ref('account_financial_report.a_recv')
        self.a_view = self.ref('account_financial_report.a_view')
        self.a_cons = self.ref('account_financial_report.a_cons')
        self.a_view_cons = self.ref('account_financial_report.a_view_cons')
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
            'fiscalyear_id': self.fiscalyear_id,
            'display_account_level': 0,
            'target_move': 'posted',
            'tot_check': False,
            'periods': [],
            'account_list': [],
        }

    def _get_afr_template(self):
        values = dict(self.values)
        values = dict(
            values,
            name='AFR REPORT',
            account_ids=[(4, self.a_recv, 0)],
            fiscalyear_id=self.fiscalyear_id,
        )
        values.pop('periods')
        values.pop('fiscalyear_id')
        values.pop('account_list')
        return self.afr_obj.create(values)

    def test_lines_report_afr_view_account_period_all(self):
        _logger.info('Testing View Account at All Period')
        values = dict(
            self.values,
            display_account_level=6,
            account_list=[(4, self.a_view, 0)],
        )
        lines = self._generate_afr(values)
        if not lines:
            self.assertTrue(False, 'Something went wrong with Test')

        self.assertEqual(len(lines), 6, 'There should be 6 Lines')

        lines = lines[0]
        self.assertEqual(lines.get('id'), self.a_view, 'Wrong Account')
        self.assertEqual(lines.get('balanceinit'), 500)
        self.assertEqual(lines.get('debit'), 500)
        self.assertEqual(lines.get('credit'), 500)
        self.assertEqual(lines.get('balance'), 500)
        self.assertEqual(lines.get('ytd'), 0)

        _logger.info('Testing View Account at All Period (Multicurrency)')
        values = dict(
            values,
            currency_id=self.ref('base.USD'),
        )
        lines = self._generate_afr(values)
        if not lines:
            self.assertTrue(False, 'Something went wrong with Test')

        self.assertEqual(len(lines), 6, 'There should be 6 Lines')

        lines = lines[0]
        self.assertEqual(lines.get('id'), self.a_view, 'Wrong Account')
        self.assertNotEqual(lines.get('balanceinit'), 500)
        self.assertNotEqual(lines.get('debit'), 500)
        self.assertNotEqual(lines.get('credit'), 500)
        self.assertNotEqual(lines.get('balance'), 500)
        self.assertEqual(lines.get('ytd'), 0)

    def test_lines_report_afr_consview_account_period_all(self):
        _logger.info('Testing Consolidated & View Account at All Period')
        values = dict(
            self.values,
            display_account_level=6,
            account_list=[(4, self.a_view_cons, 0)],
        )
        lines = self._generate_afr(values)
        if not lines:
            self.assertTrue(False, 'Something went wrong with Test')

        self.assertEqual(len(lines), 3, 'There should be 3 Lines')

        lines = lines[0]
        self.assertEqual(lines.get('id'), self.a_view_cons, 'Wrong Account')
        self.assertEqual(lines.get('balanceinit'), 500)
        self.assertEqual(lines.get('debit'), 500)
        self.assertEqual(lines.get('credit'), 500)
        self.assertEqual(lines.get('balance'), 500)
        self.assertEqual(lines.get('ytd'), 0)

    def test_lines_report_afr_consolidated_account_period_all(self):
        _logger.info('Testing Consolidated Account at All Period')
        values = dict(
            self.values,
            display_account_level=6,
            account_list=[(4, self.a_cons, 0)],
        )
        lines = self._generate_afr(values)
        if not lines:
            self.assertTrue(False, 'Something went wrong with Test')

        self.assertEqual(len(lines), 1, 'There should be 1 Lines')

        lines = lines[0]
        self.assertEqual(lines.get('id'), self.a_cons, 'Wrong Account')
        self.assertEqual(lines.get('balanceinit'), 500)
        self.assertEqual(lines.get('debit'), 500)
        self.assertEqual(lines.get('credit'), 500)
        self.assertEqual(lines.get('balance'), 500)
        self.assertEqual(lines.get('ytd'), 0)

    def test_lines_report_afr_pay_period_01(self):
        _logger.info('Testing Payables at Period 01')
        values = dict(
            self.values,
            periods=[(4, self.period_1, 0)],
            account_list=[(4, self.a_pay, 0)]
        )
        lines = self._generate_afr(values)
        if lines and lines[0]:
            lines = lines[0]
            self.assertEqual(lines.get('id'), self.a_pay, 'Wrong Account')
            self.assertEqual(lines.get('balanceinit'), -500)
            self.assertEqual(lines.get('debit'), 0)
            self.assertEqual(lines.get('credit'), 0)
            self.assertEqual(lines.get('balance'), -500)
            self.assertEqual(lines.get('ytd'), 0)
        else:
            self.assertTrue(False, 'Something went wrong with Test')

    def test_lines_report_afr_pay_period_03_is_one_col(self):
        _logger.info('Testing Payables at Period 03 One Column')
        values = dict(
            self.values,
            columns='one',
            periods=[(4, self.period_3, 0)],
            account_list=[(4, self.a_pay, 0)],
            inf_type='IS',
        )
        lines = self._generate_afr(values)
        if lines and lines[0]:
            lines = lines[0]
            self.assertEqual(lines.get('id'), self.a_pay, 'Wrong Account')
            self.assertEqual(lines.get('balance'), -300)
            self.assertEqual(lines.get('ytd'), -300)
        else:
            self.assertTrue(False, 'Something went wrong with Test')

    def test_lines_report_afr_pay_period_03(self):
        _logger.info('Testing Payables at Period 03')
        values = dict(
            self.values,
            periods=[(4, self.period_3, 0)],
            account_list=[(4, self.a_pay, 0)],
        )
        lines = self._generate_afr(values)
        if lines and lines[0]:
            lines = lines[0]
            self.assertEqual(lines.get('id'), self.a_pay, 'Wrong Account')
            self.assertEqual(lines.get('balanceinit'), -500)
            self.assertEqual(lines.get('debit'), 0)
            self.assertEqual(lines.get('credit'), 300)
            self.assertEqual(lines.get('balance'), -800)
            self.assertEqual(lines.get('ytd'), -300)
        else:
            self.assertTrue(False, 'Something went wrong with Test')

    def test_lines_report_partner_balance_period_05(self):
        _logger.info('Testing Partner Balance at Period 05')
        values = dict(
            self.values,
            periods=[(4, self.period_5, 0)],
            account_list=[(4, self.a_recv, 0), (4, self.a_pay, 0)],
            partner_balance=True,
        )
        lines = self._generate_afr(values)

        if not lines:
            self.assertTrue(False, 'Something went wrong with Test')

        self.assertEqual(len(lines), 2, 'There should be 2 Lines')
        for elem in zip(PARTNER_BALANCE, lines):
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
                for elem2 in zip(std.get(col), res.get(col)):
                    std2, res2 = elem2
                    for col2 in std2:
                        self.assertEqual(
                            res2.get(col2), std2[col2],
                            'Something went wrong for %s' % col2)

        _logger.info('Testing Partner Balance at Period 01 With no Lines')
        values = dict(
            values,
            periods=[(4, self.period_1, 0)],
            account_list=[(4, self.srv, 0)],
            partner_balance=True,
        )
        lines = self._generate_afr(values)

        if lines:
            self.assertTrue(False, 'Something went wrong with Test')

    def test_lines_report_journal_ledger_period_03(self):
        _logger.info('Testing Journal Ledger at Period 03')
        values = dict(
            self.values,
            periods=[(4, self.period_3, 0)],
            account_list=[(4, self.a_pay, 0)],
            journal_ledger=True,
        )
        lines = self._generate_afr(values)

        if not lines:
            self.assertTrue(False, 'Something went wrong with Test')

        self.assertEqual(len(lines), 1, 'There should be 1 Lines')
        for elem in zip(JOURNAL_LEDGER, lines):
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
                for elem2 in zip(std.get(col), res.get(col)):
                    std2, res2 = elem2
                    for col2 in std2:
                        self.assertEqual(
                            res2.get(col2), std2[col2],
                            'Something went wrong for %s' % col2)

    def test_lines_report_analytic_ledger_period_03(self):
        _logger.info('Testing Analytic Ledger at Period 03')
        values = dict(
            self.values,
            periods=[(4, self.period_3, 0)],
            account_list=self.account_list,
            analytic_ledger=True,
        )
        lines = self._generate_afr(values)
        if not lines:
            self.assertTrue(False, 'Something went wrong with Test')

        self.assertEqual(len(lines), 3, 'There should be 3 Lines')
        for elem in zip(ANALYTIC_LEDGER, lines):
            std, res = elem
            for col in std:
                if col == 'mayor':
                    self.assertEqual(
                        len(res.get(col)), len(std[col]),
                        'Something went wrong for %s' % col)
                    for elem2 in zip(std.get(col), res.get(col)):
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
        values = dict(
            self.values,
            display_account='all',
            periods=[(4, self.period_3, 0)],
            account_list=self.account_list,
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

    def test_lines_report_afr_pay_period_05_two_cols(self):
        _logger.info('Testing Payables at Period 05')
        values = dict(
            self.values,
            periods=[(4, self.period_5, 0)],
            columns='two',
            account_list=[(4, self.a_pay, 0)],
        )
        lines = self._generate_afr(values)
        if lines and lines[0]:
            lines = lines[0]
            self.assertEqual(lines.get('id'), self.a_pay, 'Wrong Account')
            self.assertEqual(lines.get('balanceinit'), -800)
            self.assertEqual(lines.get('debit'), 0)
            self.assertEqual(lines.get('credit'), 0)
            self.assertEqual(lines.get('balance'), -800)
            self.assertEqual(lines.get('ytd'), 0)
        else:
            self.assertTrue(False, 'Something went wrong with Test')

    def test_lines_report_afr_pay_period_05_five_cols(self):
        _logger.info('Testing Payables at Period 05')
        values = dict(
            self.values,
            periods=[(4, self.period_5, 0)],
            columns='five',
            account_list=[(4, self.a_pay, 0)],
        )
        lines = self._generate_afr(values)
        if lines and lines[0]:
            lines = lines[0]
            self.assertEqual(lines.get('id'), self.a_pay, 'Wrong Account')
            self.assertEqual(lines.get('balanceinit'), -800)
            self.assertEqual(lines.get('debit'), 0)
            self.assertEqual(lines.get('credit'), 0)
            self.assertEqual(lines.get('balance'), -800)
            self.assertEqual(lines.get('ytd'), 0)
        else:
            self.assertTrue(False, 'Something went wrong with Test')

    def test_lines_report_afr_pay_period_05(self):
        _logger.info('Testing Payables at Period 05')
        values = dict(
            self.values,
            periods=[(4, self.period_5, 0)],
            account_list=[(4, self.a_pay, 0)],
        )
        lines = self._generate_afr(values)
        if lines and lines[0]:
            lines = lines[0]
            self.assertEqual(lines.get('id'), self.a_pay, 'Wrong Account')
            self.assertEqual(lines.get('balanceinit'), -800)
            self.assertEqual(lines.get('debit'), 0)
            self.assertEqual(lines.get('credit'), 0)
            self.assertEqual(lines.get('balance'), -800)
            self.assertEqual(lines.get('ytd'), 0)
        else:
            self.assertTrue(False, 'Something went wrong with Test')

    def test_lines_report_afr_pay_period_all(self):
        _logger.info('Testing Payables All Periods')
        values = dict(
            self.values,
            account_list=[(4, self.a_pay, 0)],
        )
        lines = self._generate_afr(values)
        if lines and lines[0]:
            lines = lines[0]
            self.assertEqual(lines.get('id'), self.a_pay, 'Wrong Account')
            self.assertEqual(lines.get('change_sign'), -1)
            self.assertEqual(lines.get('balanceinit'), -500)
            self.assertEqual(lines.get('debit'), 0)
            self.assertEqual(lines.get('credit'), 300)
            self.assertEqual(lines.get('balance'), -800)
            self.assertEqual(lines.get('ytd'), -300)
        else:
            self.assertTrue(False, 'Something went wrong with Test')

    def test_rec_qtr(self):
        _logger.info('Testing Receivables at Quarter Cols')
        values = dict(
            self.values,
            columns='qtr',
            inf_type='BS',
            display_account='mov',
            periods=[],
            account_list=[(4, self.a_recv, 0)],
        )
        lines = self._generate_afr(values)
        if lines and lines[0]:
            res = lines[0]
            self.assertEqual(
                res.get('change_sign'), 1, 'Sign should be positive')
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
        values = dict(
            self.values,
            columns='thirteen',
            inf_type='BS',
            periods=[],
            account_list=[(4, self.a_recv, 0)],
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

    def test_chart0_account(self):
        _logger.info('Testing Receivables at Period 05')
        values = dict(
            self.values,
            account_list=[(4, self.chart0, 0)],
        )
        lines = self._generate_afr(values)

        if not lines:
            # /!\ NOTE: Weak Test
            self.assertTrue(False, 'Something went wrong with Test')

    def test_rec_period_05_is(self):
        _logger.info('Testing Receivables at Period 05')
        values = dict(
            self.values,
            inf_type='IS',
            tot_check=True,
            periods=[(4, self.period_5, 0)],
            account_list=[(4, self.a_recv, 0)],
        )
        lines = self._generate_afr(values)
        if lines and lines[0]:
            res = lines[0]
            self.assertEqual(res.get('type'), 'receivable')
            self.assertEqual(res.get('id'), self.a_recv, 'Wrong Account')
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
        company_id = self.ref('base.main_company')
        company_brw = self.env['res.company'].browse(company_id)
        company_brw.country_id = False
        company_brw.vat = ''
        values = dict(
            self.values,
            periods=[(4, self.period_5, 0)],
            account_list=[(4, self.a_recv, 0)],
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

        company_brw.country_id = self.ref('base.ve')
        company_brw.vat = 'VEJ123456789'
        res = AccountBalance(
            self.cr, self.uid, '', {}).get_vat_by_country(
                data['data']['form'])
        if res and res[0]:
            res = res[0]
            self.assertEqual(res, '- J-12345678-9')
        else:
            self.assertTrue(False, 'Something went wrong with Test')

        company_brw.country_id = self.ref('base.mx')
        company_brw.vat = 'MXABC980101T1B'
        res = AccountBalance(
            self.cr, self.uid, '', {}).get_vat_by_country(
                data['data']['form'])
        if res and res[0]:
            res = res[0]
            self.assertEqual(res, 'ABC980101T1B')
        else:
            self.assertTrue(False, 'Something went wrong with Test')

        company_brw.country_id = self.ref('base.us')
        company_brw.vat = 'US1234567890'
        res = AccountBalance(
            self.cr, self.uid, '', {}).get_vat_by_country(
                data['data']['form'])
        if res and res[0]:
            res = res[0]
            self.assertEqual(res, 'US1234567890')
        else:
            self.assertTrue(False, 'Something went wrong with Test')
        return True

    def test_get_informe_text(self):
        _logger.info('Testing Inform Text')
        values = dict(
            self.values,
            periods=[(4, self.period_5, 0)],
            account_list=[(4, self.a_recv, 0)],
        )
        data = self._get_data(values)
        res = AccountBalance(
            self.cr, self.uid, '', {}).get_informe_text(
                data['data']['form'])
        self.assertEqual(res, 'Balance Sheet')
        values = dict(
            values,
            analytic_ledger=True,
        )
        data = self._get_data(values)
        res = AccountBalance(
            self.cr, self.uid, '', {}).get_informe_text(
                data['data']['form'])
        self.assertEqual(res, 'Analytic Ledger')
        values = dict(
            values,
            analytic_ledger=False,
            inf_type='IS',
        )
        data = self._get_data(values)
        res = AccountBalance(
            self.cr, self.uid, '', {}).get_informe_text(
                data['data']['form'])
        self.assertEqual(res, 'Income Statement')

        values = dict(
            values,
            afr_id=self._get_afr_template().id,
        )
        data = self._get_data(values)
        res = AccountBalance(
            self.cr, self.uid, '', {}).get_informe_text(
                data['data']['form'])
        self.assertEqual(res, 'AFR REPORT')
        return True

    def test_get_month(self):
        _logger.info('Testing Month')
        values = dict(
            self.values,
            periods=[(4, self.period_5, 0)],
            account_list=[(4, self.a_recv, 0)],
        )
        data = self._get_data(values)
        res = AccountBalance(
            self.cr, self.uid, '', {}).get_month(
                data['data']['form'])
        self.assertEqual(res, 'From 05/01/{year} to 05/31/{year}'.format(
            year=time.strftime('%Y')))
        return True

    def _get_data(self, values):

        wiz_id = self.wiz_rep_obj.create(values)

        context = {
            'xls_report': True,
            'active_model': 'wizard.report',
            'active_ids': [wiz_id.id],
            'active_id': wiz_id.id,
        }
        return wiz_id.with_context(context).print_report()

    def _generate_afr(self, values):
        data = self._get_data(values)
        return AccountBalance(
            self.cr, self.uid, '', {}).lines(data['data']['form'])

    def test_onchange_company_id(self):
        values = dict(
            self.values,
            periods=[(4, self.period_5, 0)],
            account_list=[(4, self.a_recv, 0)],
        )
        wiz_brw = self.wiz_rep_obj.create(values)
        wiz_brw.onchange_company_id()

        self.assertEqual(wiz_brw.company_id.id, self.company_id)

    def test_onchange_columns(self):
        values = dict(
            self.values,
            periods=[(4, self.period_5, 0)],
            account_list=[(4, self.a_recv, 0)],
            analytic_ledger=True,
            currency_id=self.ref('base.USD'),
            columns='five',
        )
        wiz_brw = self.wiz_rep_obj.create(values)
        wiz_brw.onchange_columns()

        self.assertEqual(wiz_brw.columns, 'five')
        self.assertEqual(wiz_brw.analytic_ledger, False)
        self.assertEqual(wiz_brw.currency_id.id, self.ref('base.USD'))
        self.assertEqual(len(wiz_brw.periods), 1)

    def test_onchange_analytic_ledger(self):
        values = dict(
            self.values,
            periods=[(4, self.period_5, 0)],
            account_list=[(4, self.a_recv, 0)],
            analytic_ledger=True,
            currency_id=self.ref('base.USD'),
        )
        wiz_brw = self.wiz_rep_obj.create(values)
        wiz_brw.onchange_analytic_ledger()

        self.assertEqual(wiz_brw.analytic_ledger, True)
        self.assertEqual(wiz_brw.currency_id.id, self.currency_id)

    def test_onchange_inf_type(self):
        values = dict(
            self.values,
            periods=[(4, self.period_5, 0)],
            account_list=[(4, self.a_recv, 0)],
            inf_type='IS',
            analytic_ledger=True,
        )
        wiz_brw = self.wiz_rep_obj.create(values)
        wiz_brw.onchange_inf_type()

        self.assertEqual(wiz_brw.inf_type, 'IS')
        self.assertEqual(wiz_brw.analytic_ledger, False)

    def test_onchange_afr_id(self):
        values = dict(
            self.values,
            account_list=[(4, self.a_recv, 0)],
        )
        wiz_brw = self.wiz_rep_obj.create(values)
        wiz_brw.onchange_afr_id()

        self.assertEqual(wiz_brw.afr_id.id, False)
        self.assertEqual(len(wiz_brw.periods), 0)

        wiz_brw.write({'afr_id': self.afr_id})
        wiz_brw.onchange_afr_id()
        self.assertEqual(wiz_brw.afr_id.id, self.afr_id)
        self.assertEqual(len(wiz_brw.periods), 2)

    def test_afr_copy(self):
        afr_brw = self.afr_obj.browse(self.afr_id)
        new_afr_brw = afr_brw.copy()
        self.assertEqual(new_afr_brw.name, 'Copy of Trial Balance')
        self.assertEqual(len(new_afr_brw.period_ids), 2)

        new_afr_brw = afr_brw.copy()
        self.assertEqual(new_afr_brw.name, 'Copy of Trial Balance (2)')
