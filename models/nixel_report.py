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
import datetime
from datetime import timedelta

from openerp.osv import osv
from openerp.report import report_sxw

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

    def _default_accounts(self):
        # buscar los parners
        pool = self.pool['res.partner']
        ids = pool.search(self.cr, self.uid, [])
        # me quedo con el primero
        ids = [ids[0]]
        for pp in pool.browse(self.cr, self.uid, ids):
            # obtengo las cuentas
            rec_account = pp.property_account_receivable.id
            pay_account = pp.property_account_payable.id
        return {'property_account_receivable': rec_account,
                'property_account_payable': pay_account,
                'expenses': 155
                }

    def _period(self):
        # get from, to dates from wizard
        wiz = self.pool['tablero_nixel.wiz_report_nixel']
        ids = wiz.search(self.cr, self.uid, [])
        for data in wiz.browse(self.cr, self.uid, ids):
            date_from = data.desde_date
            date_to = data.hasta_date
        return date_from, date_to

    def _compute_invoices(self, date_from, date_to, journal_type):
        """
        Compute all invoices from sales or purchases
        """
#        print '>>> compute_invoices from ',journal_type, date_from, date_to
        # find journals of type journal_type
        journal_pool = self.pool['account.journal']
        journal_ids = journal_pool.search(self.cr, self.uid,
                                          [('type', '=', journal_type)])
        debit = credit = 0.0
        for journal in journal_pool.browse(self.cr, self.uid, journal_ids):
            # find move lines of this journal, between dates
            pool = self.pool['account.move.line']
            ids = pool.search(self.cr, self.uid, [
                ('journal_id', '=', journal.id),
                ('date', '>=', date_from),
                ('date', '<=', date_to),
            ])
            # summarize
            for account in pool.browse(self.cr, self.uid, ids):
                if account.name != 'Gestionar Cobranzas':
#                    if account.debit != 0.0:
#                        print '...',account.debit, account.credit, account.date,' name ' ,account.name, \
#                            account.narration, account.partner_id.name, account.journal_id.name

                    debit += account.debit
                    credit += account.credit

#        print 'total > ',debit
#        print '<<< compute_invoices'
        return debit, credit

    def _compute_vouchers(self, date_from, date_to, voucher_type):
#        print '>>> compute vouchers from', voucher_type
        # find vouchers type voucher type
        voucher_pool = self.pool['account.voucher']
        voucher_ids = voucher_pool.search(self.cr, self.uid, [
            ('type', '=', voucher_type),
            ('date', '>=', date_from),
            ('date', '<=', date_to)
        ])
        amount = 0.0
        for voucher in voucher_pool.browse(self.cr, self.uid, voucher_ids):
#            print '...',voucher.amount, voucher.name, voucher.partner_id.name
            # summarize
            amount += voucher.amount

#        print '<<< compute vouchers'
        return amount

    def _compute_balance(self, cr, uid, account_id):
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
        Sumariza la cuenta account_id en elementos del diario sobre un
        período dando el total de créditos y débitos en un diccionario.
        """
        accounts = self.pool['account.move.line']
        ids = accounts.search(cr, uid, [
            ('account_id', '=', account_id),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
        ])
        debit = credit = 0.0
        for account in accounts.browse(cr, uid, ids):
            debit += account.debit
            credit += account.credit
        return {'debit': debit, 'credit': credit}

    def _compute_pos(self):
        """
        Computa todos los cobros del pos entre dos fechas
        """
#        print '>>> compute pos'
        date_from, date_to = self._period()
        # add a day to date_to
        dt = datetime.datetime.strptime(date_to,'%Y-%m-%d') + datetime.timedelta(days=1)
        date_to = dt.strftime('%Y-%m-%d')
        pos = self.pool['pos.order']
        ids = pos.search(self.cr, self.uid, [
            ('date_order', '>=', date_from+' 03:00:00'),
            ('date_order', '<=', date_to+' 03:00:00'),
        ])
        amount = 0.0
        for pos in pos.browse(self.cr, self.uid, ids):
#            print '...................................',pos.amount_total, pos.date_order
            amount += pos.amount_total
#        print 'total >', amount
#        print '<<< compute pos'
        return amount

    def _get_debtors(self):
        """
        Obtiene todoss los partners que deben y sus deudas, no tiene fecha
        """
        debtors = []
        total = 0.0
        clientes = self._default_accounts()['property_account_receivable']
        elements = self._compute_balance(self.cr, self.uid, clientes)
        for element in elements:
            if element[0] <> 0:
                debtors.append({'amount': element[0], 'name': element[1]})
                total += element[0]
        return {'debtors': debtors, 'total': total}

    def _get_creditors(self):
        """
        Obtiene todos los partners a los que se le debe deben y las deudas no tiene fecha
        """
        creditors = []
        total = 0.0
        proveedores = self._default_accounts()['property_account_payable']
        elements = self._compute_balance(self.cr, self.uid, proveedores)
        for element in elements:
            if element[0] <> 0:
                creditors.append({'amount': element[0], 'name': element[1]})
                total += element[0]
        return {'creditors': creditors, 'total': total}

    def _get_venta(self):
        """
        Facturado:
            suma todas las facturas del periodo de facturacion (no pos)
            le resta todas las notas de crédito del periodo
            le suma los movimientos del pos

        Cobrado:
            suma todos los vouchers del periodo
            le suma los movimientos del punto de venta del periodo.
        """
        date_from, date_to = self._period()
        invoiced = 0.0
        # compute sales
        sale, dummy = self._compute_invoices(date_from, date_to, 'sale')
        invoiced += sale
        # compute refunds
        refund, dummy = self._compute_invoices(date_from, date_to, 'sale_refund')
        invoiced -= refund
        invoiced += self._compute_pos()

        # cobros de facturas
        amount = self._compute_vouchers(date_from, date_to, 'receipt')
        # cobros de tickets
        amount += self._compute_pos()

#        print '=================== venta fac', invoiced, '  cob',amount
        return {'fac': invoiced,
                'cob': amount,
                'pen': invoiced - amount}

    def _get_compra(self):
        """
        Facturado:
            suma todas las facturas del periodo
            le resta todas las notas de crédito del periodo

        Cobrado:
            suma todos los vouchers del periodo
        """
        date_from, date_to = self._period()
        invoiced = 0.0
        # compute all purchases
        purchase, dummy = self._compute_invoices(date_from, date_to, 'purchase')
        invoiced += purchase
        # compute all purchase refunds
        refund, dummy = self._compute_invoices(date_from, date_to, 'purchase_refund')
        invoiced -= refund

        amount = self._compute_vouchers(date_from, date_to, 'payment')

        return {'fac': invoiced,
                'cob': amount,
                'pen': invoiced - amount}

    def _get_gastos(self):
        date_from, date_to = self._period()
        gastos = self._default_accounts()['expenses']
        dic = self._summarize_account(self.cr, self.uid, gastos,
                                      date_from, date_to)
        return {'gas': dic['debit']}


class report_nixel_class(osv.AbstractModel):
    _name = 'report.tablero_nixel.nixel_report'
    _inherit = 'report.abstract_report'
    _template = 'tablero_nixel.nixel_report'
    _wrapped_report_class = nixel_report_def

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
