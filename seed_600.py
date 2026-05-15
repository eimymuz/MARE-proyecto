import random
from datetime import date, timedelta, datetime
from django.utils import timezone
from apps.clientes.models import Cliente
from apps.embarcaciones.models import Embarcacion, TipoBarco
from apps.solicitudes.models import Solicitud, SolicitudHistorial
from apps.asignaciones.models import Administrador, Asignacion
from apps.muelles.models import Muelle, Espacio

FECHA_INICIO = date(2026, 1, 1)
FECHA_FIN    = date(2026, 5, 14)
TOTAL        = 600

ESPACIOS = {
    'A': [5030,5031,5032,5033,5034,5035,5036,5037,5038,5039,5040,5041,5042,5043,5044,5045],
    'B': [5057,5058,5059,5060,5061,5062,5063,5064,5065,5066,5067,5068,5069,5070,5071,5072,5073,5074,5075,5076,5077,5078,5079],
    'C': [5098,5099,5100,5101,5102,5103,5104,5105,5106,5107,5108,5109,5110,5111,5112,5113,5114,5115,5116,5117,5118,5119,5120,5121,5122,5123,5124,5125,5126,5127,5128,5129,5130],
    'D': [5148,5149,5150,5151,5152,5153,5154,5155,5156,5157,5158,5159,5160,5161,5162,5163,5164,5165,5166,5167,5168,5169,5170,5171,5172,5173,5174,5175,5176,5177,5178,5179,5180,5181,5182,5183,5184,5185,5186,5187,5188,5189],
    'E': [5212,5213,5214,5215,5216,5217,5218,5219,5220,5221,5222,5223,5224,5225,5226,5227,5228,5229,5230,5231,5232,5233,5234,5235,5236,5237,5238,5239,5240,5241,5242,5243,5244,5245,5246,5247,5248,5249,5250,5251,5252,5253],
    'F': [5277,5278,5279,5280,5281,5282,5283,5284,5285,5286,5287,5288,5289,5290,5291,5292,5293],
    'G': [5304,5305,5306,5307,5308,5309,5310,5311,5312,5313,5314,5315,5316,5317,5318,5319,5320,5321,5322,5323,5324,5325,5326,5327,5328,5329,5330,5331,5332,5333,5334,5335,5336],
    'H': [5089],
}

MOTIVOS_RECHAZO = [
    'EMBARCACION FUERA DE DIMENSIONES PERMITIDAS',
    'DOCUMENTACION INCOMPLETA',
    'ESPACIO NO DISPONIBLE EN LAS FECHAS SOLICITADAS',
    'CLIENTE CON ADEUDO PENDIENTE',
    'TIPO DE EMBARCACION NO PERMITIDO',
    'FECHAS DE ESTANCIA CONFLICTIVAS',
    'FALTA DE SEGURO VIGENTE',
    'EMBARCACION CON RESTRICCIONES MIGRATORIAS',
    'CALADO EXCEDE LA PROFUNDIDAD DEL MUELLE',
    'ESLORA SUPERA EL LIMITE PERMITIDO',
]

CLIENTES_DATA = [
    ('JAMES MORRISON',      '+12125550011', 'james.morrison@seed.com'),
    ('LUCIA FERNANDEZ',     '+52312100021', 'lucia.fernandez@seed.com'),
    ('ROBERT KLEIN',        '+49301234567', 'robert.klein@seed.com'),
    ('SOFIA REYES',         '+52312100031', 'sofia.reyes@seed.com'),
    ('PIERRE DUPONT',       '+33123456789', 'pierre.dupont@seed.com'),
    ('YUKI TANAKA',         '+81312345678', 'yuki.tanaka@seed.com'),
    ('CARLOS MENDEZ',       '+52312100041', 'carlos.mendez@seed.com'),
    ('ANNE LARSEN',         '+4523456789',  'anne.larsen@seed.com'),
    ('MICHAEL TORRES',      '+12125550022', 'michael.torres@seed.com'),
    ('VALENTINA CRUZ',      '+52312100051', 'valentina.cruz@seed.com'),
    ('HANS MUELLER',        '+49301234568', 'hans.mueller@seed.com'),
    ('ISABELLA ROSSI',      '+39023456789', 'isabella.rossi@seed.com'),
    ('DEREK WASHINGTON',    '+12125550033', 'derek.washington@seed.com'),
    ('CAMILA VARGAS',       '+52312100061', 'camila.vargas@seed.com'),
    ('ERIK JOHANSSON',      '+46701234567', 'erik.johansson@seed.com'),
    ('MARIA SANTOS',        '+55112345678', 'maria.santos@seed.com'),
    ('THOMAS WEBER',        '+49301234569', 'thomas.weber@seed.com'),
    ('ELENA PETROVA',       '+79161234567', 'elena.petrova@seed.com'),
    ('JUAN CASTILLO',       '+52312100071', 'juan.castillo@seed.com'),
    ('SARAH CONNORS',       '+12125550044', 'sarah.connors@seed.com'),
    ('LUCA FERRARI',        '+39023456790', 'luca.ferrari@seed.com'),
    ('AMARA DIALLO',        '+22112345678', 'amara.diallo@seed.com'),
    ('KEVIN ODUYA',         '+23412345678', 'kevin.oduya@seed.com'),
    ('NATALIA ROMERO',      '+52312100081', 'natalia.romero@seed.com'),
    ('PATRICK OBRIEN',      '+35312345678', 'patrick.obrien@seed.com'),
    ('HIROSHI YAMAMOTO',    '+81312345679', 'hiroshi.yamamoto@seed.com'),
    ('CLAUDIA MORETTI',     '+39023456791', 'claudia.moretti@seed.com'),
    ('WILLIAM BANKS',       '+12125550055', 'william.banks@seed.com'),
    ('ALEJANDRA NUNEZ',     '+52312100091', 'alejandra.nunez@seed.com'),
    ('FREDRIK LINDQVIST',   '+46701234568', 'fredrik.lindqvist@seed.com'),
    ('DIANA POPESCU',       '+40712345678', 'diana.popescu@seed.com'),
    ('MARCO GUTIERREZ',     '+52312100101', 'marco.gutierrez@seed.com'),
    ('FATIMA AL-RASHID',    '+97112345678', 'fatima.alrashid@seed.com'),
    ('CHEN WEI',            '+86212345678', 'chen.wei@seed.com'),
    ('PABLO ACOSTA',        '+52312100111', 'pablo.acosta@seed.com'),
    ('ANNIKA BERGSTROM',    '+46701234569', 'annika.bergstrom@seed.com'),
    ('DMITRI VOLKOV',       '+79161234568', 'dmitri.volkov@seed.com'),
    ('GRACE OKONKWO',       '+23412345679', 'grace.okonkwo@seed.com'),
    ('RODRIGO PEREIRA',     '+55112345679', 'rodrigo.pereira@seed.com'),
    ('LISA ANDERSON',       '+12125550066', 'lisa.anderson@seed.com'),
    ('OMAR HASSAN',         '+97112345679', 'omar.hassan@seed.com'),
    ('INGRID HAUGEN',       '+4723456789',  'ingrid.haugen@seed.com'),
    ('FELIPE SOTO',         '+52312100121', 'felipe.soto@seed.com'),
    ('PRIYA SHARMA',        '+91112345678', 'priya.sharma@seed.com'),
    ('NICOLAS BERNARD',     '+33123456790', 'nicolas.bernard@seed.com'),
    ('AKOSUA MENSAH',       '+23312345678', 'akosua.mensah@seed.com'),
    ('JORGE IBARRA',        '+52312100131', 'jorge.ibarra@seed.com'),
    ('KATARINA NOVAK',      '+38512345678', 'katarina.novak@seed.com'),
    ('BRENDAN MCCARTHY',    '+35312345679', 'brendan.mccarthy@seed.com'),
    ('YOLANDA HERRERA',     '+52312100141', 'yolanda.herrera@seed.com'),
]

BARCOS_DATA = [
    ('SEA HAWK',         'VELERO',    12.0, 4.0, 1.5),
    ('PACIFICO',         'CATAMARÁN', 15.0, 7.0, 1.5),
    ('NORDIC STAR',      'VELERO',    9.0,  3.5, 1.2),
    ('BELLA VITA',       'YATE',      18.0, 5.5, 2.0),
    ('CORAL DREAM',      'VELERO',    11.0, 4.2, 1.4),
    ('BRISE DE MER',     'YATE',      22.0, 6.8, 2.3),
    ('SAKURA MARU',      'VELERO',    8.0,  3.0, 1.1),
    ('OCEAN SPIRIT',     'CATAMARÁN', 14.0, 5.0, 1.8),
    ('VIENTO SUR',       'VELERO',    10.0, 3.8, 1.3),
    ('GRAND BLEU',       'YATE',      25.0, 7.5, 2.5),
    ('ESTRELLA MAR',     'CATAMARÁN', 16.0, 5.2, 1.9),
    ('WHITE DOLPHIN',    'VELERO',    13.0, 4.5, 1.6),
    ('SIRENA NEGRA',     'VELERO',    20.0, 6.0, 2.1),
    ('TEQUILA SUNSET',   'CATAMARÁN', 17.0, 5.8, 2.0),
    ('AURORA BOREALIS',  'YATE',      30.0, 8.0, 3.0),
    ('PLAYA AZUL',       'VELERO',    7.5,  2.8, 1.0),
    ('MARLIN AZUL',      'CATAMARÁN', 12.5, 4.3, 1.6),
    ('COSTA ALEGRE',     'VELERO',    9.5,  3.6, 1.3),
    ('LA NAVIDAD',       'YATE',      19.0, 6.2, 2.2),
    ('BAHIA GRANDE',     'CATAMARÁN', 11.5, 4.0, 1.5),
    ('LUNA LLENA',       'VELERO',    8.5,  3.2, 1.1),
    ('AGUA MARINA',      'YATE',      21.0, 6.5, 2.4),
    ('SOL Y MAR',        'CATAMARÁN', 13.5, 4.8, 1.7),
    ('BRISA TROPICAL',   'VELERO',    10.5, 3.9, 1.4),
    ('HORIZONTE',        'YATE',      24.0, 7.2, 2.6),
    ('PERLA DEL MAR',    'VELERO',    11.0, 4.0, 1.5),
    ('AVENTURA',         'CATAMARÁN', 16.5, 5.5, 2.0),
    ('ESPERANZA',        'VELERO',    9.0,  3.4, 1.2),
    ('LIBERTAD',         'YATE',      20.5, 6.3, 2.3),
    ('ISLA BONITA',      'CATAMARÁN', 14.5, 5.2, 1.8),
    ('MAR ABIERTO',      'VELERO',    12.0, 4.1, 1.5),
    ('OCEANO AZUL',      'YATE',      23.0, 7.0, 2.5),
    ('VELA BLANCA',      'VELERO',    8.0,  3.1, 1.0),
    ('RAYO DE SOL',      'CATAMARÁN', 15.5, 5.3, 1.9),
    ('NOCHE ESTRELLADA', 'YATE',      27.0, 7.8, 2.8),
    ('DELFIN AZUL',      'VELERO',    10.0, 3.7, 1.3),
    ('CAPITAN MORGAN',   'YATE',      18.5, 5.8, 2.1),
    ('CALYPSO',          'CATAMARÁN', 13.0, 4.6, 1.7),
    ('POSEIDON',         'YATE',      26.0, 7.5, 2.7),
    ('TRITÓN',           'VELERO',    11.5, 4.2, 1.5),
    ('NEPTUNO',          'CATAMARÁN', 14.0, 5.0, 1.8),
    ('SIRENA',           'VELERO',    9.5,  3.5, 1.2),
    ('ATLAS',            'YATE',      22.5, 6.7, 2.4),
    ('CRONOS',           'VELERO',    10.5, 3.9, 1.4),
    ('ZEUS',             'YATE',      28.0, 8.0, 3.0),
    ('HERMES',           'CATAMARÁN', 12.0, 4.3, 1.6),
    ('APOLO',            'VELERO',    8.5,  3.2, 1.1),
    ('ARES',             'YATE',      19.5, 6.0, 2.2),
    ('ARTEMISA',         'VELERO',    11.0, 4.0, 1.4),
    ('AFRODITA',         'CATAMARÁN', 15.0, 5.4, 1.9),
]

COMENTARIOS = [
    '', '', '', '', '',
    'REQUIERE SERVICIO ELECTRICO 30A',
    'REQUIERE SERVICIO ELECTRICO 50A',
    'PRIMERA VISITA A LA MARINA',
    'SOLICITA ESPACIO CERCA DE LA ENTRADA',
    'EMBARCACION CON MASCOTA A BORDO',
    'REQUIERE CONEXION DE AGUA POTABLE',
    'TRIPULACION DE 4 PERSONAS',
]

def fecha_rand(inicio, fin):
    return inicio + timedelta(days=random.randint(0, (fin - inicio).days))

def dt_rand(fecha):
    dt = datetime.combine(fecha, datetime.min.time()).replace(
        hour=random.randint(8, 18), minute=random.randint(0, 59))
    return timezone.make_aware(dt)

def crear_historial(sol, estados, fecha_base):
    SolicitudHistorial.objects.filter(solicitud=sol).delete()
    ant = None
    offset = 0
    for estado in estados:
        offset += random.randint(1, 4)
        fecha = min(fecha_base + timedelta(days=offset), FECHA_FIN)
        h = SolicitudHistorial(solicitud=sol, estado_anterior=ant, estado_nuevo=estado)
        h.save()
        SolicitudHistorial.objects.filter(pk=h.pk).update(fecha_cambio=dt_rand(fecha))
        ant = estado

# Cargar objetos
admins    = {pk: Administrador.objects.get(pk=pk) for pk in [2,4,5,6,7]}
tipos_map = {t.tipo_barco: t for t in TipoBarco.objects.all()}
muelles   = {m.nombre: m for m in Muelle.objects.all()}

for nombre in ['VELERO','CATAMARÁN','YATE','LANCHA','MOTONAVE']:
    if nombre not in tipos_map:
        t, _ = TipoBarco.objects.get_or_create(tipo_barco=nombre)
        tipos_map[nombre] = t

# Distribución: 70% COMPLETADA, 15% APROBADA, 10% RECHAZADA, 5% otros
estados_pool = (
    ['COMPLETADA'] * 420 +
    ['APROBADA']   * 90  +
    ['RECHAZADA']  * 60  +
    ['EN_ESPERA']  * 18  +
    ['PENDIENTE']  * 12
)
random.shuffle(estados_pool)

espacios_usados = {}

def espacio_libre(pk, inicio, fin):
    for (i, f) in espacios_usados.get(pk, []):
        if not (fin < i or inicio > f):
            return False
    return True

def reservar(pk, inicio, fin):
    espacios_usados.setdefault(pk, []).append((inicio, fin))

pesos_muelles = ['B']*9 + ['C']*9 + ['D']*9 + ['G']*9 + ['E']*6 + ['F']*5 + ['A']*4 + ['H']*1

creadas = 0
for i in range(TOTAL):
    cd  = CLIENTES_DATA[i % len(CLIENTES_DATA)]
    cliente, _ = Cliente.objects.get_or_create(
        email=cd[2], defaults={'fullname': cd[0], 'telefono': cd[1]})

    bd  = BARCOS_DATA[i % len(BARCOS_DATA)]
    tipo = tipos_map.get(bd[1], list(tipos_map.values())[0])
    emb, _ = Embarcacion.objects.get_or_create(
        cliente=cliente, nombre_bote=bd[0],
        defaults={'tipo_barco': tipo, 'eslora': bd[2], 'manga': bd[3], 'calado': bd[4]})

    estado_final = estados_pool[i]
    fecha_sol = fecha_rand(FECHA_INICIO, FECHA_FIN - timedelta(days=12))
    duracion  = random.randint(3, 28)
    fecha_ll  = fecha_sol + timedelta(days=random.randint(2, 8))
    fecha_sa  = fecha_ll  + timedelta(days=duracion)

    sol = Solicitud(
        embarcacion=emb,
        fecha_llegada=fecha_ll,
        fecha_salida=fecha_sa,
        estado=estado_final,
        primera_entrada_mexico=random.random() < 0.15,
        comentario=random.choice(COMENTARIOS),
    )
    if estado_final == 'RECHAZADA':
        sol.motivo_rechazo = random.choice(MOTIVOS_RECHAZO)
    Solicitud.save(sol)
    Solicitud.objects.filter(pk=sol.pk).update(fecha_solicitud=fecha_sol)

    cadenas = {
        'PENDIENTE':  ['PENDIENTE'],
        'EN_ESPERA':  ['PENDIENTE', 'EN_ESPERA'],
        'APROBADA':   ['PENDIENTE', 'EN_ESPERA', 'APROBADA'],
        'COMPLETADA': ['PENDIENTE', 'EN_ESPERA', 'APROBADA', 'COMPLETADA'],
        'RECHAZADA':  random.choice([
            ['PENDIENTE', 'RECHAZADA'],
            ['PENDIENTE', 'EN_ESPERA', 'RECHAZADA'],
            ['PENDIENTE', 'EN_ESPERA', 'APROBADA', 'RECHAZADA'],
        ]),
    }
    crear_historial(sol, cadenas[estado_final], fecha_sol)

    if estado_final in ('APROBADA', 'COMPLETADA'):
        nombre_m = random.choice(pesos_muelles)
        esp_pks  = list(ESPACIOS[nombre_m])
        random.shuffle(esp_pks)

        esp_pk = next((pk for pk in esp_pks if espacio_libre(pk, fecha_ll, fecha_sa)), None)
        if esp_pk is None:
            nombre_m = 'F'
            esp_pk   = random.choice(ESPACIOS['F'])

        reservar(esp_pk, fecha_ll, fecha_sa)
        esp_obj    = Espacio.objects.get(pk=esp_pk)
        muelle_obj = muelles[nombre_m]
        admin1     = admins[random.choice([5, 6, 7])]

        asig = Asignacion.objects.create(
            solicitud=sol, muelle=muelle_obj, administrador=admin1,
            fecha_inicio=fecha_ll, fecha_fin=fecha_sa, activa=True)
        asig.espacios.set([esp_obj])

        # reasignación ~25%
        if random.random() < 0.25:
            asig.activa = False
            asig.save()

            nombre_m2 = random.choice(['B','C','D','G','E','F'])
            esp_pks2  = list(ESPACIOS[nombre_m2])
            random.shuffle(esp_pks2)
            esp2_pk = esp_pks2[0]
            reservar(esp2_pk, fecha_ll, fecha_sa)

            admin2 = admins[random.choice([pk for pk in [5,6,7] if admins[pk] != admin1])]
            asig2  = Asignacion.objects.create(
                solicitud=sol, muelle=muelles[nombre_m2], administrador=admin2,
                fecha_inicio=fecha_ll, fecha_fin=fecha_sa, activa=True)
            asig2.espacios.set([Espacio.objects.get(pk=esp2_pk)])

    creadas += 1
    if creadas % 50 == 0:
        print(f'  {creadas}/{TOTAL} completadas...')

print(f'\nListo — {creadas} solicitudes creadas.')
