from odoo import models, fields, api

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    panelhex_data_ids = fields.One2many('panelhex.workorder.data', 'workorder_id', string='Datos Hexamex')

    @api.model
    def create(self, vals):
        res = super(MrpWorkorder, self).create(vals)
        if res.workcenter_id:
            self.create_default_workorder_data(res)
        return res

    def create_default_workorder_data(self, workorder):
        WorkorderData = self.env['panelhex.workorder.data']
        workcenter_code = workorder.workcenter_id.code
        if workcenter_code == 'OCT':
            default_fields = [
                ('entrada_rollo_lote', 'char'),
                ('entrada_rollo_proveedor', 'many2one'),
                ('entrada_rollo_peso', 'float'),
                ('entrada_rollo_gramaje', 'float'),
                ('entrada_rollo_medidas', 'char'),
                ('salida_num_corridas', 'integer'),
                ('salida_tipo_hexagono', 'char'),
                ('operador', 'many2one'),
                ('fecha', 'date'),
            ]
        elif workcenter_code == 'COR':
            default_fields = [
                ('entrada_lote_bloque', 'char'),
                ('salida_num_cortes', 'integer'),
                ('operador', 'many2one'),
                ('fecha', 'date'),
            ]
        elif workcenter_code == 'PEG':
            default_fields = [
                ('salida_num_reticulas', 'integer'),
                ('salida_lote_tarima', 'char'),
                ('fecha_pegado', 'date'),
                ('operador', 'many2one'),
            ]
        elif workcenter_code == 'LAM':
            default_fields = [
                ('entrada_reticula_lote', 'char'),
                ('entrada_rollo_superior_lote', 'char'),
                ('entrada_rollo_inferior_lote', 'char'),
                ('salida_metros_lineales', 'float'),
                ('salida_especificacion', 'char'),
                ('cliente', 'many2one'),
                ('codigo_producto', 'char'),
                ('merma_generada', 'float'),
                ('kg_pegamento_utilizado', 'float'),
                ('operador', 'many2one'),
                ('fecha', 'date'),
            ]
        elif workcenter_code == 'REM':
            default_fields = [
                ('entrada_tablero_lote', 'char'),
                ('salida_num_tarimas', 'integer'),
                ('salida_especificacion', 'char'),
                ('cliente', 'many2one'),
                ('codigo_producto', 'char'),
                ('merma_generada', 'float'),
                ('operador', 'many2one'),
                ('fecha', 'date'),
            ]
        else:
            default_fields = []  # Default empty list for unknown workcenter codes

        for field, field_type in default_fields:
            WorkorderData.create({
                'workorder_id': workorder.id,
                'name': field,
                'field_type': field_type,
            })

class PanelhexWorkorderData(models.Model):
    _name = 'panelhex.workorder.data'
    _description = 'Panelhex Workorder Data'

    workorder_id = fields.Many2one('mrp.workorder', string='Work Order', required=True, ondelete='cascade')
    name = fields.Char(string='Field Name', required=True)
    field_type = fields.Selection([
        ('char', 'Text'),
        ('float', 'Number'),
        ('integer', 'Integer'),
        ('many2one', 'Relation'),
        ('date', 'Date'),
    ], string='Field Type', required=True)
    value_char = fields.Char(string='Text Value')
    value_float = fields.Float(string='Number Value')
    value_integer = fields.Integer(string='Integer Value')
    value_many2one = fields.Many2one('res.partner', string='Relation Value')
    value_date = fields.Date(string='Date Value')