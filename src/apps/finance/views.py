from django.shortcuts import render
from django.views.generic import ListView, TemplateView
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import PaymentSummary, PaymentTransaction
from apps.core.models import Family, FamilyMember
from django.db.models import Q
from datetime import datetime

# Create your views here.

class FamilyPaymentDatesView(LoginRequiredMixin, ListView):
    template_name = 'finance/family_payment_dates.html'
    context_object_name = 'payment_dates'

    def get_family(self):
        """Get the family object from the URL parameter."""
        return get_object_or_404(Family, id=self.kwargs.get('family_id'))

    def get_queryset(self):
        """Get all unique payment dates for the family's parents."""
        family = self.get_family()
        
        # Get parent members (both male and female)
        parents = FamilyMember.objects.filter(
            family=family,
            member_type='parent'
        ).select_related('user')
        
        # Get all payment summaries for these parents
        payment_summaries = PaymentSummary.objects.filter(
            customer__in=[parent.user for parent in parents]
        ).order_by('-date')
        
        # Get unique dates
        return payment_summaries.dates('date', 'day', order='DESC')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['family'] = self.get_family()
        return context

class FamilyPaymentDetailsView(LoginRequiredMixin, TemplateView):
    template_name = 'finance/family_payment_details.html'

    def get_family(self):
        """Get the family object from the URL parameter."""
        return get_object_or_404(Family, id=self.kwargs.get('family_id'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        family = self.get_family()
        payment_date = datetime.strptime(self.kwargs.get('date'), '%Y-%m-%d').date()
        
        # Get parent members
        parents = FamilyMember.objects.filter(
            family=family,
            member_type='parent'
        ).select_related('user')
        
        # Get all payment summaries for the given date
        payment_summaries = PaymentSummary.objects.filter(
            customer__in=[parent.user for parent in parents],
            date=payment_date
        ).select_related('payment_transaction', 'customer')
        
        # Organize payments by type
        payments_by_type = {
            'fee': [],
            'wallet_top_up': [],
            'discount_top_up_for_family': [],
            'product_sale': []
        }
        
        for summary in payment_summaries:
            details = summary.details
            payment_type = details.get('type')
            
            if payment_type == 'fee':
                payments_by_type['fee'].append({
                    'summary': summary,
                    'details': details
                })
            elif payment_type == 'wallet_top_up':
                payments_by_type['wallet_top_up'].append({
                    'summary': summary,
                    'details': details
                })
            elif payment_type == 'discount_top_up_for_family':
                payments_by_type['discount_top_up_for_family'].append({
                    'summary': summary,
                    'details': details
                })
            elif payment_type == 'product_sale':
                payments_by_type['product_sale'].append({
                    'summary': summary,
                    'details': details
                })
        
        context.update({
            'family': family,
            'payment_date': payment_date,
            'payments_by_type': payments_by_type,
            'has_payments': any(payments_by_type.values())
        })
        
        return context
