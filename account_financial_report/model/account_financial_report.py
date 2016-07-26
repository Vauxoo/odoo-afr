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
    """Provides a Prototyping class to be reused to hold templates & wizards"""

    _name = "afr"
    _inherit = "afr.abstract"  # pylint: disable=R7980

    name = fields.Char('Name', size=128, required=True)

    @api.multi
    def copy(self, default=None):
        """Duplicate a record and changes its name to make it unique"""
        default = dict(default or {})
        new_name = _('Copy of %s') % self.name
        lst = self.search([('name', 'like', new_name)])
        if lst:
            new_name = u'%s (%s)' % (new_name, len(lst) + 1)
        default['name'] = new_name
        return super(AccountFinancialReport, self).copy(default=default)
