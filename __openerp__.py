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

{
    "name": "Tablero de mando Nixel",
    "version": "1.0",
    "author": "jeo Software",
    'website': 'http://www.jeo-soft.com.ar',
    "depends": ["product", "purchase", "sale"],
    "category": "Tools",
    "description": """
Tablero de mando Nixel
----------------------
  Genera un reporte con indicadores de gestión
  Nota: Para que el reporte tome los estilos poner en parametros:
    report.url    http://0.0.0.0:8069
""",
    "init_xml": [],
    "demo_xml": [],
    "data": [

        "views/nixel_report.xml",
        "wizard/report_wizard_view.xml"
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
