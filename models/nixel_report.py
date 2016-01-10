# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import time

from openerp.osv import osv
from openerp.report import report_sxw

_PROVEEDORES = 79
_DEUDORES_POR_VENTAS = 8
_GASTOS = 155

class nixel_report_def(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(nixel_report_def, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_debtors': self._get_debtors,
            'get_creditors': self._get_creditors,
            'get_venta': self._get_venta,
            'get_compra': self._get_compra,
            'get_gastos': self._get_gastos,
        })

    def _get_default_accounts(self):
        # buscar los parners
        pool = self.pool['res.partner']
        ids = pool.search(self.cr, self.uid, [])
        # me quedo con el primero
        ids = [ids[0]]
        for pp in pool.browse(self.cr, self.uid, ids):
            # obtengo las cuentas
            rec_account = pp.property_account_receivable.id
            pay_account = pp.property_account_payable.id
            print 'deud', rec_account, '        pay', pay_account
        return {'property_account_receivable': rec_account,
                'property_account_payable': pay_account,
                'expenses': 155
                }

    def _get_period(self):
        # get from, to dates from wizard
        wiz = self.pool['tablero_nixel.wiz_report_nixel']
        ids = wiz.search(self.cr, self.uid, [])
        for data in wiz.browse(self.cr, self.uid, ids):
            date_from = data.desde_date
            date_to = data.hasta_date
        return date_from, date_to

    def _get_compute_balance(self, cr, uid, account_id):
        """
        Obtiene una lista de los registros en una cuenta conciliable, indicando nombre
        del partner y monto adeudado
        """
        accounts = self.pool['account.account']
        ids = accounts.search(cr, uid, [('id', '=', account_id)])
        result = []
        for account in accounts.browse(cr, uid, ids):
            type = account.type

            if type == 'receivable':
                sumarg = 'debit-credit'
            else:
                sumarg = 'credit-debit'

            cr.execute("""
                select sum(%s) as balance,  res_partner.name
                from account_move_line
                inner join res_partner
                on res_partner.id = account_move_line.partner_id
                where account_id = %s
                group by partner_id, res_partner.name
                """ % (sumarg, account_id))
            result = cr.fetchall()
        return result

    def _summarize_account(self, cr, uid, account_id, date_from, date_to):
        """
        Sumariza la cuenta account_id en elementos del elementos del diario sobre un
        período dando el total de créditos y débitos en un diccionario.
        """
        accounts = self.pool['account.move.line']
        ids = accounts.search(cr, uid, [('account_id', '=', account_id),
                                        ('date', '>=', date_from),
                                        ('date', '<=', date_to),
                                        ])
        debit = credit = 0.0
        for account in accounts.browse(cr, uid, ids):
            debit += account.debit
            credit += account.credit
        return {'debit': debit, 'credit': credit}

    def _get_debtors(self):
        debtors = []
        total = 0.0
        clientes = self._get_default_accounts()['property_account_receivable']
        elements = self._get_compute_balance(self.cr, self.uid, clientes)
        for element in elements:
            if element[0] <> 0:
                debtors.append({'amount': element[0], 'name': element[1]})
                total += element[0]
        return {'debtors': debtors, 'total': total}

    def _get_creditors(self):
        creditors = []
        total = 0.0
        proveedores = self._get_default_accounts()['property_account_payable']
        elements = self._get_compute_balance(self.cr, self.uid, proveedores)
        for element in elements:
            if element[0] <> 0:
                creditors.append({'amount': element[0], 'name': element[1]})
                total += element[0]
        return {'creditors': creditors, 'total': total}

    def _get_venta(self):
        date_from, date_to = self._get_period()
        clientes = self._get_default_accounts()['property_account_receivable']
        dic = self._summarize_account(self.cr, self.uid, clientes,
                                      date_from, date_to)
        return {'fac': dic['debit'], 'cob': dic['credit'],
                'pen': dic['debit'] - dic['credit']}

    def _get_compra(self):
        date_from, date_to = self._get_period()
        proveedores = self._get_default_accounts()['property_account_payable']
        dic = self._summarize_account(self.cr, self.uid, proveedores,
                                      date_from, date_to)
        return {'fac': dic['credit'], 'cob': dic['debit'],
                'pen': dic['credit'] - dic['debit']}

    def _get_gastos(self):
        date_from, date_to = self._get_period()
        gastos = self._get_default_accounts()['expenses']
        dic = self._summarize_account(self.cr, self.uid, gastos,
                                      date_from, date_to)
        return {'gas': dic['debit']}


class report_nixel_class(osv.AbstractModel):
    _name = 'report.tablero_nixel.nixel_report'
    _inherit = 'report.abstract_report'
    _template = 'tablero_nixel.nixel_report'
    _wrapped_report_class = nixel_report_def

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
