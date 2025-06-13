from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from ..models import BillOfMaterials, BOMComponent
from Inventory.models import Item

class ProductBOMsAPIView(LoginRequiredMixin, View):
    """API view to get BOMs for a specific product (Item)"""
    
    def get(self, request, product_id):
        try:
            # Check permissions
            if not request.user.has_perm('Production.view_billofmaterials'):
                raise PermissionDenied("You don't have permission to view BOMs")
            
            product = get_object_or_404(Item, id=product_id)
            boms = BillOfMaterials.objects.filter(product=product, status='Active').order_by('code')
            
            bom_data = []
            for bom in boms:
                bom_data.append({
                    'id': bom.id,
                    'code': bom.code,
                    'name': bom.name,
                    'bom_type': bom.bom_type,
                    'status': bom.status,
                    'x_quantity': float(bom.x_quantity),
                })
            
            return JsonResponse({
                'success': True,
                'boms': bom_data,
                'product_name': product.name,
                'product_code': getattr(product, 'code', ''),
            })
            
        except PermissionDenied as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=403)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

class BOMComponentsAPIView(LoginRequiredMixin, View):
    """API view to get components for a specific BOM"""
    
    def get(self, request, bom_id):
        try:
            # Check permissions
            if not request.user.has_perm('Production.view_bomcomponent'):
                raise PermissionDenied("You don't have permission to view BOM components")
            
            bom = get_object_or_404(BillOfMaterials, id=bom_id)
            components = BOMComponent.objects.filter(bom=bom).order_by('item_code')
            
            component_data = []
            for component in components:
                component_data.append({
                    'id': component.id,
                    'item_code': component.item_code,
                    'item_name': component.item_name,
                    'quantity': float(component.quantity),
                    'unit': component.unit or 'PCS',
                    'unit_price': float(component.unit_price),
                    'total': float(component.total),
                })
            
            return JsonResponse({
                'success': True,
                'components': component_data,
                'bom_name': bom.name,
                'bom_code': bom.code,
                'bom_type': bom.bom_type,
                'x_quantity': float(bom.x_quantity),
                'total_components': len(component_data),
            })
            
        except PermissionDenied as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=403)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

class ProductInfoAPIView(LoginRequiredMixin, View):
    """API view to get product (Item) information"""
    
    def get(self, request, product_id):
        try:
            # Check permissions
            if not request.user.has_perm('Inventory.view_item'):
                raise PermissionDenied("You don't have permission to view items")
            
            product = get_object_or_404(Item, id=product_id)
            
            product_data = {
                'id': product.id,
                'name': product.name,
                'code': getattr(product, 'code', ''),
                'description': getattr(product, 'description', ''),
                'category': getattr(product, 'category', ''),
                'status': getattr(product, 'status', 'Active'),
            }
            
            # Get available BOMs for this product
            boms = BillOfMaterials.objects.filter(product=product, status='Active')
            bom_data = []
            for bom in boms:
                bom_data.append({
                    'id': bom.id,
                    'code': bom.code,
                    'name': bom.name,
                    'bom_type': bom.bom_type,
                    'x_quantity': float(bom.x_quantity),
                })
            
            product_data['boms'] = bom_data
            
            return JsonResponse({
                'success': True,
                'product': product_data,
            })
            
        except PermissionDenied as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=403)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
