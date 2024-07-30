# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def remove_data(self, o, s=[]):
        for line in o:
            try:
                if not self.env['ir.model']._get(line):
                    continue
            except Exception as e:
                _logger.warning('remove data error get ir.model: %s,%s', line, e)
                continue
            obj_name = line
            obj = self.pool.get(obj_name)
            if not obj:
                t_name = obj_name.replace('.', '_')
            else:
                t_name = obj._table
            sql = "delete from %s" % t_name
            try:
                self._cr.execute(sql)
                self._cr.commit()
            except Exception as e:
                _logger.warning('remove data error: %s,%s', line, e)
        for line in s:
            domain = ['|', ('code', '=ilike', line + '%'), ('prefix', '=ilike', line + '%')]
            try:
                seqs = self.env['ir.sequence'].sudo().search(domain)
                if seqs.exists():
                    seqs.write({
                        'number_next': 1,
                    })
            except Exception as e:
                _logger.warning('reset sequence data error: %s,%s', line, e)
        return True
    
    def remove_sales(self):
        to_removes = [
            'sale.order.line',
            'sale.order',
        ]
        seqs = [
            'sale',
        ]
        return self.remove_data(to_removes, seqs)

    def remove_product(self):
        to_removes = [
            'product.product',
            'product.template',
        ]
        seqs = [
            'product.product',
        ]
        return self.remove_data(to_removes, seqs)

    def remove_product_attribute(self):
        to_removes = [
            'product.attribute.value',
            'product.attribute',
        ]
        seqs = []
        return self.remove_data(to_removes, seqs)

    def remove_pos(self):
        to_removes = [
            'pos.payment',
            'pos.order.line',
            'pos.order',
            'pos.session',
        ]
        seqs = [
            'pos.',
        ]
        res = self.remove_data(to_removes, seqs)
        try:
            statement = self.env['account.bank.statement'].sudo().search([])
            for s in statement:
                s._end_balance()
        except Exception as e:
            _logger.error('reset sequence data error: %s', e)
        return res

    def remove_purchase(self):
        to_removes = [
            'purchase.order.line',
            'purchase.order',
            'purchase.requisition.line',
            'purchase.requisition',
        ]
        seqs = [
            'purchase.',
        ]
        return self.remove_data(to_removes, seqs)

    def remove_expense(self):
        to_removes = [
            'hr.expense.sheet',
            'hr.expense',
            'hr.payslip',
            'hr.payslip.run',
        ]
        seqs = [
            'hr.expense.',
        ]
        return self.remove_data(to_removes, seqs)

    def remove_mrp(self):
        to_removes = [
            'mrp.workcenter.productivity',
            'mrp.workorder',
            'mrp.production.workcenter.line',
            'change.production.qty',
            'mrp.production',
            'mrp.production.product.line',
            'mrp.unbuild',
            'change.production.qty',
            'sale.forecast.indirect',
            'sale.forecast',
        ]
        seqs = [
            'mrp.',
        ]
        return self.remove_data(to_removes, seqs)

    def remove_mrp_bom(self):
        to_removes = [
            'mrp.bom.line',
            'mrp.bom',
        ]
        seqs = []
        return self.remove_data(to_removes, seqs)

    def remove_inventory(self):
        to_removes = [
            'stock.quant',
            'stock.move.line',
            'stock.package_level',
            'stock.quantity.history',
            'stock.quant.package',
            'stock.move',
            'stock.picking',
            'stock.scrap',
            'stock.picking.batch',
            'stock.inventory.line',
            'stock.inventory',
            'stock.valuation.layer',
            'stock.lot',
            'procurement.group',
        ]
        seqs = [
            'stock.',
            'picking.',
            'procurement.group',
            'product.tracking.default',
            'WH/',
        ]
        return self.remove_data(to_removes, seqs)

    def remove_account(self):
        to_removes = [
            'payment.transaction',
            'account.bank.statement.line',
            'account.payment',
            'account.analytic.line',
            'account.analytic.account',
            'account.partial.reconcile',
            'account.move.line',
            'hr.expense.sheet',
            'account.move',
        ]
        res = self.remove_data(to_removes, [])
        domain = [
            ('company_id', '=', self.env.company.id),
            '|', ('code', '=ilike', 'account.%'),
            '|', ('prefix', '=ilike', 'BNK1/%'),
            '|', ('prefix', '=ilike', 'CSH1/%'),
            '|', ('prefix', '=ilike', 'INV/%'),
            '|', ('prefix', '=ilike', 'EXCH/%'),
            '|', ('prefix', '=ilike', 'MISC/%'),
            '|', ('prefix', '=ilike', '账单/%'),
            ('prefix', '=ilike', '杂项/%')
        ]
        try:
            seqs = self.env['ir.sequence'].search(domain)
            if seqs.exists():
                seqs.write({
                    'number_next': 1,
                })
        except Exception as e:
            _logger.error('reset sequence data error: %s,%s', domain, e)
        return res

    def remove_account_chart(self):
        company_id = self.env.company.id
        self = self.with_context(force_company=company_id, company_id=company_id)
        to_removes = [
            'res.partner.bank',
            'account.move.line',
            'account.invoice',
            'account.payment',
            'account.bank.statement',
            'account.tax.account.tag',
            'account.tax',
            'account.account.account.tag',
            'wizard_multi_charts_accounts',
            'account.journal',
            'account.account',
        ]
        try:
            field1 = self.env['ir.model.fields']._get('product.template', "taxes_id").id
            field2 = self.env['ir.model.fields']._get('product.template', "supplier_taxes_id").id

            sql = "delete from ir_default where (field_id = %s or field_id = %s) and company_id=%d" \
                  % (field1, field2, company_id)
            sql2 = "update account_journal set bank_account_id=NULL where company_id=%d;" % company_id
            self._cr.execute(sql)
            self._cr.execute(sql2)

            self._cr.commit()
        except Exception as e:
            _logger.error('remove data error: %s,%s', 'account_chart: set tax and account_journal', e)
        if self.env['ir.model']._get('pos.config'):
            self.env['pos.config'].write({
                'journal_id': False,
            })
        try:
            rec = self.env['res.partner'].search([])
            for r in rec:
                r.write({
                    'property_account_receivable_id': None,
                    'property_account_payable_id': None,
                })
        except Exception as e:
            _logger.error('remove data error: %s,%s', 'account_chart', e)
        try:
            rec = self.env['product.category'].search([])
            for r in rec:
                r.write({
                    'property_account_income_categ_id': None,
                    'property_account_expense_categ_id': None,
                    'property_account_creditor_price_difference_categ': None,
                    'property_stock_account_input_categ_id': None,
                    'property_stock_account_output_categ_id': None,
                    'property_stock_valuation_account_id': None,
                })
        except Exception as e:
            pass
        try:
            rec = self.env['product.template'].search([])
            for r in rec:
                r.write({
                    'property_account_income_id': None,
                    'property_account_expense_id': None,
                })
        except Exception as e:
            pass
        try:
            rec = self.env['stock.location'].search([])
            for r in rec:
                r.write({
                    'valuation_in_account_id': None,
                    'valuation_out_account_id': None,
                })
        except Exception as e:
            pass
        seqs = []
        res = self.remove_data(to_removes, seqs)
        self.env.company.write({'chart_template': False})
        return res

    def remove_project(self):
        to_removes = [
            'account.analytic.line',
            'project.task',
            'project.forecast',
            'project.project',
        ]
        seqs = []
        return self.remove_data(to_removes, seqs)

    def remove_quality(self):
        to_removes = [
            'quality.check',
            'quality.alert',
        ]
        seqs = [
            'quality.check',
            'quality.alert',
        ]
        return self.remove_data(to_removes, seqs)

    def remove_quality_setting(self):
        to_removes = [
            'quality.point',
            'quality.alert.stage',
            'quality.alert.team',
            'quality.point.test_type',
            'quality.reason',
            'quality.tag',
        ]
        return self.remove_data(to_removes)

    def remove_website(self):
        to_removes = [
            'blog.tag.category',
            'blog.tag',
            'blog.post',
            'blog.blog',
            'product.wishlist',
            'website.published.multi.mixin',
            'website.published.mixin',
            'website.multi.mixin',
            'website.visitor',
            'website.redirect',
            'website.seo.metadata',
        ]
        seqs = []
        return self.remove_data(to_removes, seqs)

    def remove_message(self):
        to_removes = [
            'mail.message',
            'mail.followers',
            'mail.activity',
        ]
        seqs = []
        return self.remove_data(to_removes, seqs)

    def remove_payslip_line(self):
        to_removes = [
            'hr.payslip.line'
        ]
        return self.remove_data(to_removes)

    def remove_contract(self):
        to_removes = [
            'hr.payslip.line',
            'hr.work.entry',
            'hr.contract'
        ]
        return self.remove_data(to_removes)

    def remove_salary_attachment(self):
        to_removes = [
            'hr.salary.attachment'
        ]
        return self.remove_data(to_removes)        

    def remove_contract_salary_offer(self):
        to_removes = [
            'hr.contract.salary.offer'
        ]
        return self.remove_data(to_removes)

    def remove_work_entry(self):
        to_removes = [
            'hr.work.entry'
        ]
        return self.remove_data(to_removes)
    
    def remove_payslip(self):
        to_removes = [
            'hr.payslip'
        ]
        return self.remove_data(to_removes)
    
    def remove_payslip_run(self):
        to_removes = [
            'hr.payslip.run'
        ]
        return self.remove_data(to_removes)

    def remove_payroll_structure(self):
        to_removes = [
            'hr.salary.rule',
            'hr.payroll.structure'
        ]
        return self.remove_data(to_removes)

    def remove_payroll_structure_type(self):
        to_removes = [
            'hr.salary.rule',
            'hr.payroll.structure',
            'hr.payroll.structure.type'
        ]
        return self.remove_data(to_removes)

    def remove_work_entry_type(self):
        to_removes = [
            'hr.payslip.line',
            'hr.salary.rule',
            'hr.payslip.worked.days',
            'hr.payroll.structure',
            'hr.payroll.structure.type',
            'hr.work.entry.type'
        ]
        return self.remove_data(to_removes)

    def remove_salary_rule(self):
        to_removes = [
            'hr.payslip.line',
            'hr.salary.rule'
        ]
        return self.remove_data(to_removes)

    def remove_payroll(self):
        to_removes = [
            'hr.work.entry',
            'hr.payslip.line',
            'hr.contract',
            'hr.salary.attachment',
            'hr.contract.salary.offer',
            'hr.payslip',
            'hr.payslip.run',
            'hr.salary.rule',
            'hr.payroll.structure',
            'hr.payroll.structure.type',
            'hr.work.entry.type'
        ]
        return self.remove_data(to_removes)

    def remove_helpdesk_ticket(self):
        to_removes = [
            'helpdesk.ticket'
        ]
        seqs = [
            'helpdesk.ticket'
        ]      
        return self.remove_data(to_removes, seqs)

    def remove_helpdesk_sla(self):
        to_removes = [
            'helpdesk.sla'
        ]
        return self.remove_data(to_removes)
    
    def remove_helpdesk(self):
        to_removes = [
            'helpdesk.ticket',
            'helpdesk.sla',
            'helpdesk.team'
        ]
        seqs = [
            'helpdesk.ticket'
        ] 
        return self.remove_data(to_removes, seqs)

    def remove_frontdesk_visitor(self):
        to_removes = [
            'frontdesk.visitor'
        ]
        return self.remove_data(to_removes)

    def remove_frontdesk(self):
        to_removes = [
            'frontdesk.visitor',
            'frontdesk.frontdesk'
        ]
        return self.remove_data(to_removes)

    def remove_attendance(self):
        to_removes = [
            'hr.attendance'
        ]
        seqs = []
        return self.remove_data(to_removes, seqs)

    def remove_leave_accural_plan(self):
        to_removes = [
            'hr.leave.accrual.plan'
        ]
        return self.remove_data(to_removes)
    
    def remove_leave_allocation(self):
        to_removes = [
            'hr.leave.allocation'
        ]
        return self.remove_data(to_removes)

    def remove_leave_type(self):
        to_removes = [
            'hr.leave',
            'hr.leave.allocation',
            'hr.leave.type',
        ]
        return self.remove_data(to_removes)

    def remove_resource_calendar_leaves(self):
        to_removes = [
            'resource.calendar.leaves'
        ]
        return self.remove_data(to_removes)

    def remove_leave_mandatory_day(self):
        to_removes = [
            'hr.leave.mandatory.day'
        ]
        return self.remove_data(to_removes)

    def remove_mail_activity(self):
        to_removes = [
            'mail.activity'
        ]
        return self.remove_data(to_removes)

    def remove_mail_activity_plan_template(self):
        to_removes = [
            'mail.activity.plan.template'
        ]
        return self.remove_data(to_removes)

    def remove_mail_activity_type(self):
        to_removes = [
            'mail.activity.type'
        ]
        return self.remove_data(to_removes)

    def remove_timeoff(self):
        to_removes = [
            'hr.leave.accrual.plan',
            'hr.leave.allocation',
            'hr.leave',
            'hr.leave.type',
            'resource.calendar.leaves',
            'hr.leave.mandatory.day',
            'mail.activity',
            'mail.activity.plan.template',
            'mail.activity.type'
        ]
        seqs = []
        return self.remove_data(to_removes, seqs)

    def remove_knowledge(self):
        to_removes = [
            'knowledge.article',
            
        ]
        seqs = []
        return self.remove_data(to_removes, seqs)


    def remove_all(self):
        self.remove_website()
        self.remove_quality_setting()
        self.remove_quality()
        self.remove_inventory()
        self.remove_purchase()
        self.remove_mrp()
        self.remove_sales()
        self.remove_project()
        self.remove_pos()
        self.remove_expense()
        self.remove_message()
        self.remove_account()
        self.remove_payroll()
        self.remove_helpdesk()
        self.remove_frontdesk()
        self.remove_attendance()
        self.remove_timeoff()
        self.remove_knowledge()
        # self.remove_account_chart()
        return True

    def reset_cat_loc_name(self):
        ids = self.env['product.category'].search([
            ('parent_id', '!=', False)
        ], order='complete_name')
        for rec in ids:
            try:
                rec._compute_complete_name()
            except:
                pass
        ids = self.env['stock.location'].search([
            ('location_id', '!=', False),
            ('usage', '!=', 'views'),
        ], order='complete_name')
        for rec in ids:
            try:
                rec._compute_complete_name()
            except:
                pass
        return True
