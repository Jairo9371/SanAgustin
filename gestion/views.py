from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.core.paginator import InvalidPage, Paginator
from django.db import DataError, IntegrityError, connection, transaction
from django.db.models import ProtectedError, Q, CharField, TextField
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from .catalogo import MODELOS, RELACIONES, ETIQUETAS, SECCIONES
from .forms import BusquedaHistorialForm, formulario_para
from .historial import consultar_historial
from .models import Paciente

class SoloPersonal(LoginRequiredMixin, UserPassesTestMixin):
    """En este proyecto académico solo las cuentas staff acceden a datos clínicos."""
    def test_func(self):
        return self.request.user.is_active and self.request.user.is_staff

def obtener_modelo(slug):
    try:
        return MODELOS[slug]
    except KeyError as exc:
        raise Http404('Tabla no disponible') from exc


def errores_de_guardado(form, error):
    """Conserva los errores de modelo, incluidos los de campos calculados."""
    if hasattr(error, 'error_dict'):
        for campo, errores in error.error_dict.items():
            destino = campo if campo in form.fields else None
            for detalle in errores:
                form.add_error(destino, detalle)
    else:
        form.add_error(None, error)

class InicioView(SoloPersonal, TemplateView):
    template_name = 'gestion/inicio.html'   
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['secciones'] = SECCIONES
        return data


@method_decorator(never_cache, name='dispatch')
class HistorialPacienteView(SoloPersonal, TemplateView):
    template_name = 'gestion/consulta_historial.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        busqueda_realizada = 'dpi' in self.request.GET
        form = BusquedaHistorialForm(self.request.GET if busqueda_realizada else None)
        data.update({
            'form': form, 'busqueda_realizada': busqueda_realizada,
            'paciente': None, 'historial': [], 'condiciones': [], 'alergias': [],
            'page_obj': None, 'paginator': None, 'is_paginated': False,
        })
        if busqueda_realizada and form.is_valid():
            paciente = Paciente.objects.filter(dpi=form.cleaned_data['dpi']).first()
            if paciente is not None:
                data['paciente'] = paciente
                data.update(consultar_historial(paciente, self.request.GET.get('page')))
        return data


class VistaModelo(SoloPersonal):
    def dispatch(self, request, *args, **kwargs):
        self.slug = kwargs['slug']
        self.model = obtener_modelo(self.slug)
        return super().dispatch(request, *args, **kwargs)
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['titulo'] = ETIQUETAS[self.slug]
        data['slug'] = self.slug
        data['campos'] = [f for f in self.model._meta.concrete_fields if not f.auto_created]
        return data

class ListadoView(VistaModelo, ListView):
    template_name = 'gestion/listado.html'
    context_object_name = 'registros'   
    paginate_by = 15
    def get_queryset(self):
        qs = self.model._default_manager.all().order_by(self.model._meta.pk.name)
        claves_foraneas = [f.name for f in self.model._meta.concrete_fields
                          if f.many_to_one or f.one_to_one]
        if claves_foraneas:
            qs = qs.select_related(*claves_foraneas)
        termino = self.request.GET.get('q', '').strip()[:100]
        if termino:
            texto = [f.name for f in self.model._meta.concrete_fields
                     if isinstance(f, (CharField, TextField))]
            if texto:
                filtro = Q()
                for campo in texto[:6]:
                    filtro |= Q(**{f'{campo}__icontains': termino})
                qs = qs.filter(filtro)
        return qs
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        # Limitar columnas para legibilidad; detalle permite ver todos los campos.
        data['columnas'] = [f for f in self.model._meta.concrete_fields if not f.auto_created][:7]
        data['q'] = self.request.GET.get('q','').strip()[:100]
        return data

class DetalleView(VistaModelo, DetailView):
    template_name = 'gestion/detalle.html'
    context_object_name = 'registro'

class CrearView(VistaModelo, CreateView):
    template_name = 'gestion/formulario.html'
    def get_form_class(self):
        return formulario_para(self.model)
    def form_valid(self, form):
        try:
            with transaction.atomic():
                result = super().form_valid(form)
            messages.success(self.request, 'Registro creado correctamente.')
            return result
        except IntegrityError:
            form.add_error(None, 'No se pudo guardar. Comprueba valores únicos y relaciones.')
            return self.form_invalid(form)
        except DataError:
            form.add_error(None, 'No se pudo guardar. Algún valor excede el tamaño o rango permitido.')
            return self.form_invalid(form)
        except ValidationError as exc:
            errores_de_guardado(form, exc)
            return self.form_invalid(form)
    def get_success_url(self):
        return reverse('gestion:detalle', kwargs={'slug': self.slug, 'pk': self.object.pk})
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['accion'] = 'Crear'
        return data

class EditarView(VistaModelo, UpdateView):
    template_name = 'gestion/formulario.html'
    context_object_name = 'registro'
    def get_form_class(self):
        return formulario_para(self.model)
    def form_valid(self, form):
        try:
            with transaction.atomic():
                result = super().form_valid(form)
            messages.success(self.request, 'Registro actualizado correctamente.')
            return result
        except IntegrityError:
            form.add_error(None, 'No se pudo actualizar. Comprueba valores únicos y relaciones.')
            return self.form_invalid(form)
        except DataError:
            form.add_error(None, 'No se pudo actualizar. Algún valor excede el tamaño o rango permitido.')
            return self.form_invalid(form)
        except ValidationError as exc:
            errores_de_guardado(form, exc)
            return self.form_invalid(form)
    def get_success_url(self):
        return reverse('gestion:detalle', kwargs={'slug': self.slug, 'pk': self.object.pk})
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['accion'] = 'Editar'
        return data

class EliminarView(VistaModelo, DeleteView):
    template_name = 'gestion/confirmar_eliminar.html'
    context_object_name = 'registro'
    def get_success_url(self):
        return reverse('gestion:listado', kwargs={'slug': self.slug})
    def form_valid(self, form):
        clave = self.object.pk
        try:
            with transaction.atomic():
                self.object.delete()
        except (ProtectedError, IntegrityError):
            messages.error(self.request, 'No se puede eliminar: existen registros relacionados con este dato.')
            return redirect('gestion:detalle', slug=self.slug, pk=clave)
        except ValidationError as exc:
            messages.error(self.request, 'No se puede eliminar: ' + '; '.join(exc.messages))
            return redirect('gestion:detalle', slug=self.slug, pk=clave)
        messages.success(self.request, 'Registro eliminado correctamente.')
        return redirect(self.get_success_url())


class RelacionesView(SoloPersonal, TemplateView):
    template_name = 'gestion/relaciones.html'
    paginate_by = 25

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        slug = kwargs['slug']

        if slug not in RELACIONES:
            raise Http404('Relación no registrada')

        item = RELACIONES[slug]

        if slug == 'medicamento_componente':
            sql = """
                SELECT
                    mc.id_medicamento,
                    mc.id_componente,
                    m.nombre_comercial,
                    ca.nombre
                FROM MEDICAMENTO_COMPONENTE AS mc
                INNER JOIN MEDICAMENTO AS m
                    ON mc.id_medicamento = m.id_medicamento
                INNER JOIN COMPONENTE_ACTIVO AS ca
                    ON mc.id_componente = ca.id_componente
                ORDER BY mc.id_medicamento, mc.id_componente
            """
            data['columnas'] = [
                'Nombre del medicamento',
                'Nombre del componente'
            ]

        else:
            columnas = ', '.join(
                f'[{col}]' for col in item['columnas']
            )
            orden = ', '.join(f'[{col}]' for col in item['columnas'][:2])
            sql = f'SELECT {columnas} FROM [{item["tabla"]}] ORDER BY {orden}'
            data['columnas'] = item['columnas']

        with connection.cursor() as cursor:
            cursor.execute(f'SELECT COUNT(*) FROM [{item["tabla"]}]')
            total = cursor.fetchone()[0]
            paginator = Paginator(range(total), self.paginate_by)
            try:
                pagina = paginator.page(self.request.GET.get('page', 1))
            except InvalidPage as exc:
                raise Http404('Página de relaciones no disponible') from exc
            desplazamiento = (pagina.number - 1) * self.paginate_by
            cursor.execute(
                sql + ' OFFSET %s ROWS FETCH NEXT %s ROWS ONLY',
                [desplazamiento, self.paginate_by],
            )
            pagina.object_list = cursor.fetchall()

        data['filas'] = pagina.object_list
        data['paginator'] = paginator
        data['page_obj'] = pagina
        data['is_paginated'] = paginator.num_pages > 1
        data['slug'] = slug
        data['titulo'] = item['nombre']

        return data
