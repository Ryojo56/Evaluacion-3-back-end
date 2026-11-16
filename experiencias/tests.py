from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from cuentas.models import Rol

from .management.commands.datos_demo import CLAVE_DEMO
from .models import Categoria, EstadoPago, Experiencia, Reserva


class FlujosPrepruebaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("datos_demo", verbosity=0)
        cls.admin = User.objects.get(username="admin_demo")
        cls.guia = User.objects.get(username="guia_norte")
        cls.otro_guia = User.objects.get(username="guia_sur")
        cls.ana = User.objects.get(username="turista_ana")
        cls.luis = User.objects.get(username="turista_luis")

    def test_datos_minimos_y_cinco_foreign_keys(self):
        from django.db import connection

        self.assertEqual(User.objects.count(), 5)
        for guia in (self.guia, self.otro_guia):
            self.assertEqual(Experiencia.objects.filter(creador=guia).count(), 4)
        for turista in (self.ana, self.luis):
            self.assertEqual(Reserva.objects.filter(usuario=turista).count(), 3)
        with connection.cursor() as cursor:
            relaciones = {
                tabla: sum(bool(c["foreign_key"]) for c in connection.introspection.get_constraints(cursor, tabla).values())
                for tabla in ("cuentas_perfil", "experiencias_experiencia", "experiencias_reserva")
            }
        self.assertEqual(relaciones, {
            "cuentas_perfil": 1, "experiencias_experiencia": 2, "experiencias_reserva": 2,
        })

    def test_sesion_login_logout_y_ruta_privada(self):
        self.assertRedirects(self.client.get(reverse("panel")), "/cuentas/entrar/?next=/panel/")
        respuesta = self.client.post(reverse("login"), {"username": "guia_norte", "password": CLAVE_DEMO})
        self.assertRedirects(respuesta, reverse("panel"))
        self.assertContains(self.client.get(reverse("panel")), "Mis experiencias")
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.assertRedirects(self.client.post(reverse("logout")), reverse("home"))
        self.assertEqual(self.client.get(reverse("experiencias")).status_code, 302)

    def test_registro_asigna_turista_aunque_envien_otro_rol(self):
        respuesta = self.client.post(reverse("signup"), {
            "username": "registro_prueba", "password1": CLAVE_DEMO, "password2": CLAVE_DEMO, "rol": "admin",
        })
        self.assertRedirects(respuesta, reverse("login"))
        self.assertEqual(User.objects.get(username="registro_prueba").perfiles.get().rol, Rol.TURISTA)

    def test_guia_tiene_acceso_solo_a_lo_propio(self):
        propia = Experiencia.objects.filter(creador=self.guia).first()
        ajena = Experiencia.objects.filter(creador=self.otro_guia).first()
        self.client.force_login(self.guia)
        listado = self.client.get(reverse("experiencias"))
        self.assertContains(listado, propia.titulo)
        self.assertNotContains(listado, ajena.titulo)
        self.assertEqual(self.client.get(reverse("experiencia_editar", args=[propia.pk])).status_code, 200)
        self.assertEqual(self.client.post(reverse("experiencia_editar", args=[ajena.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("experiencia_eliminar", args=[propia.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse("categorias")).status_code, 403)
        self.assertEqual(self.client.get(reverse("reservas")).status_code, 403)

    def test_creador_sale_de_la_sesion_y_el_guia_puede_editar(self):
        self.client.force_login(self.guia)
        datos = {
            "titulo": "Avistamiento", "descripcion": "Ruta guiada", "precio": 5000, "cupo_maximo": 4,
            "fecha_hora": (timezone.localtime() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M"),
            "categoria": Categoria.objects.first().pk, "activa": "on", "creador": self.otro_guia.pk,
        }
        self.assertRedirects(self.client.post(reverse("experiencia_nueva"), datos), reverse("experiencias"))
        experiencia = Experiencia.objects.get(titulo="Avistamiento")
        self.assertEqual(experiencia.creador, self.guia)
        datos["titulo"] = "Avistamiento de aves"
        self.assertRedirects(self.client.post(reverse("experiencia_editar", args=[experiencia.pk]), datos),
                             reverse("experiencias"))
        experiencia.refresh_from_db()
        self.assertEqual(experiencia.titulo, "Avistamiento de aves")

    def test_turista_solo_ve_y_cancela_reservas_propias_pendientes(self):
        propia = Reserva.objects.filter(usuario=self.ana, estado_pago=EstadoPago.PENDIENTE).first()
        pagada = Reserva.objects.get(usuario=self.ana, estado_pago=EstadoPago.CONFIRMADO)
        ajena = Reserva.objects.filter(usuario=self.luis).first()
        self.client.force_login(self.ana)
        self.assertEqual(list(self.client.get(reverse("reservas")).context["reservas"]),
                         list(Reserva.objects.filter(usuario=self.ana).order_by("-fecha_inscripcion")))
        self.assertEqual(self.client.post(reverse("reserva_eliminar", args=[ajena.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("reserva_eliminar", args=[pagada.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("reserva_editar", args=[propia.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse("experiencias")).status_code, 403)
        self.assertEqual(self.client.get(reverse("reserva_eliminar", args=[propia.pk])).status_code, 200)
        self.assertTrue(Reserva.objects.filter(pk=propia.pk).exists())
        self.assertRedirects(self.client.post(reverse("reserva_eliminar", args=[propia.pk])), reverse("reservas"))
        self.assertFalse(Reserva.objects.filter(pk=propia.pk).exists())

    def test_reserva_rechaza_duplicados_y_sobreventa(self):
        experiencia = Experiencia.objects.get(titulo="Arriendo de casco")
        Experiencia.objects.filter(pk=experiencia.pk).update(cupo_maximo=1)
        url = reverse("reservar", args=[experiencia.pk])
        self.client.force_login(self.ana)
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertRedirects(self.client.post(url, {"usuario": self.luis.pk, "estado_pago": "confirmado"}),
                             reverse("reservas"))
        reserva = Reserva.objects.get(experiencia=experiencia)
        self.assertEqual((reserva.usuario, reserva.estado_pago), (self.ana, EstadoPago.PENDIENTE))
        self.assertContains(self.client.post(url, follow=True), "Ya tienes una reserva")
        self.client.force_login(self.luis)
        self.assertContains(self.client.post(url, follow=True), "ya no tiene cupos")
        self.assertEqual(Reserva.objects.filter(experiencia=experiencia).count(), 1)

    def test_catalogo_oculta_experiencias_y_categorias_inactivas_y_fechas_pasadas(self):
        oculta = Experiencia.objects.get(titulo="Sendero del Coigüe")
        categoria_inactiva = Categoria.objects.get(nombre="Canopy")
        Experiencia.objects.filter(pk=oculta.pk).update(activa=False)
        Categoria.objects.filter(pk=categoria_inactiva.pk).update(activa=False)
        pasada = Experiencia.objects.get(titulo="Kayak en la laguna")
        Experiencia.objects.filter(pk=pasada.pk).update(fecha_hora=timezone.now() - timedelta(days=1))
        listado = self.client.get(reverse("catalogo"))
        for titulo in (oculta.titulo, "Canopy entre copas", pasada.titulo):
            self.assertNotContains(listado, titulo)
        self.assertContains(listado, "Arriendo de casco")
        self.client.force_login(self.ana)
        self.assertContains(self.client.post(reverse("reservar", args=[pasada.pk]), follow=True), "no está disponible")

    def test_admin_gestiona_usuarios_categorias_experiencias_y_reservas(self):
        self.client.force_login(self.admin)
        for destino in ("usuarios", "categorias", "experiencias", "reservas"):
            self.assertEqual(self.client.get(reverse(destino)).status_code, 200)
        datos = {"nombre": "Escalada", "descripcion": "Prueba", "activa": "on"}
        self.assertRedirects(self.client.post(reverse("categoria_nueva"), datos), reverse("categorias"))
        categoria = Categoria.objects.get(nombre="Escalada")
        datos["nombre"] = "Escalada guiada"
        self.assertRedirects(self.client.post(reverse("categoria_editar", args=[categoria.pk]), datos),
                             reverse("categorias"))
        categoria.refresh_from_db()
        self.assertEqual(categoria.nombre, "Escalada guiada")
        self.assertRedirects(self.client.post(reverse("categoria_eliminar", args=[categoria.pk])),
                             reverse("categorias"))
        self.assertFalse(Categoria.objects.filter(pk=categoria.pk).exists())
        experiencia = Experiencia.objects.get(titulo="Arriendo de casco")
        self.assertEqual(self.client.get(reverse("experiencia_editar", args=[experiencia.pk])).status_code, 200)
        self.assertRedirects(self.client.post(reverse("reserva_nueva"), {
            "usuario": self.ana.pk, "experiencia": experiencia.pk, "estado_pago": EstadoPago.PENDIENTE,
        }), reverse("reservas"))
        reserva = Reserva.objects.get(experiencia=experiencia, usuario=self.ana)
        self.assertRedirects(self.client.post(reverse("reserva_editar", args=[reserva.pk]), {
            "estado_pago": EstadoPago.CONFIRMADO,
        }), reverse("reservas"))
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado_pago, EstadoPago.CONFIRMADO)
        self.assertRedirects(self.client.post(reverse("reserva_eliminar", args=[reserva.pk])), reverse("reservas"))
        self.assertFalse(Reserva.objects.filter(pk=reserva.pk).exists())
        self.assertRedirects(self.client.post(reverse("experiencia_eliminar", args=[experiencia.pk])),
                             reverse("experiencias"))
        self.assertFalse(Experiencia.objects.filter(pk=experiencia.pk).exists())

    def test_admin_crea_edita_y_elimina_usuarios(self):
        self.client.force_login(self.admin)
        datos = {"username": "guia_extra", "password1": CLAVE_DEMO, "password2": CLAVE_DEMO, "rol": Rol.GUIA}
        self.assertRedirects(self.client.post(reverse("usuario_nuevo"), datos), reverse("usuarios"))
        nuevo = User.objects.get(username="guia_extra")
        self.assertEqual(nuevo.perfiles.get().rol, Rol.GUIA)
        self.assertRedirects(self.client.post(reverse("usuario_editar", args=[nuevo.pk]), {
            "username": nuevo.username, "rol": Rol.TURISTA, "is_active": "on",
        }), reverse("usuarios"))
        self.assertEqual(nuevo.perfiles.get().rol, Rol.TURISTA)
        self.assertRedirects(self.client.post(reverse("usuario_eliminar", args=[nuevo.pk])), reverse("usuarios"))
        self.assertFalse(User.objects.filter(pk=nuevo.pk).exists())

    def test_post_sin_csrf_se_rechaza(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.ana)
        experiencia = Experiencia.objects.get(titulo="Arriendo de casco")
        self.assertEqual(cliente.post(reverse("reservar", args=[experiencia.pk])).status_code, 403)

    def test_turista_paga_solo_reservas_propias_pendientes(self):
        propia = Reserva.objects.filter(usuario=self.ana, estado_pago=EstadoPago.PENDIENTE).first()
        ajena = Reserva.objects.filter(usuario=self.luis, estado_pago=EstadoPago.PENDIENTE).first()
        url = reverse("reserva_pagar", args=[propia.pk])
        self.client.force_login(self.guia)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.client.force_login(self.ana)
        self.assertEqual(self.client.post(reverse("reserva_pagar", args=[ajena.pk])).status_code, 404)
        self.assertContains(self.client.get(url), "Confirmar pago")
        self.assertRedirects(self.client.post(url), reverse("reservas"))
        propia.refresh_from_db()
        self.assertEqual(propia.estado_pago, EstadoPago.CONFIRMADO)
        self.assertContains(self.client.post(url, follow=True), "ya está pagada")
        ajena.refresh_from_db()
        self.assertEqual(ajena.estado_pago, EstadoPago.PENDIENTE)
