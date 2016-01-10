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

from openerp.osv import orm, fields
import time

class report_wizard(orm.TransientModel):
    _name = 'tablero_nixel.wiz_report_nixel'
    _columns = {
        'desde_date': fields.date('Desde', default=lambda self: self._get_default_date()),
        'hasta_date': fields.date('Hasta', default=lambda self: self._get_default_date()),
    }

    def _get_default_date(self):
        return time.strftime('%Y-%m-%d')

    def button_generate_report(self, cr, uid, ids, context=None):
        cur_obj = self.browse(cr, uid, ids, context=context)

        if not cur_obj.desde_date and not cur_obj.hasta_date:
            raise orm.except_orm('Ojo!', 'Debe especificar fecha inicial y final \
            para el reporte')

        if cur_obj.desde_date > cur_obj.hasta_date:
            raise orm.except_orm('Ojo!', 'La fech final (%s) no debe ser menor que \
                la fecha inicial (%s)' % (cur_obj.desde_date, cur_obj.hasta_date))

        data = self.read(cr, uid, ids, context=context)[0]
        datas = {
            'ids': ids,
            'model': 'tablero_nixel.wiz_report_nixel',  # wizard model name
            'form': data,
            'context': context
        }

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'tablero_nixel.nixel_report',
            'datas': datas,
        }

        # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
