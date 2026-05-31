// =============================================================================
// landing.js — Página pública de la marina (templates/publico/landing.html)
// Controla toda la interactividad del landing: internacionalización (ES/EN),
// navegación con scroll, animaciones de entrada, marquee de estadísticas,
// grilla de amenidades, calculadora de tarifas y el formulario de solicitud.
//
// No tiene dependencias externas (sin jQuery, sin librerías de terceros).
// Se carga al final del <body> en landing.html.
//
// Módulos internos:
//   I18N              → diccionario de textos ES/EN
//   applyI18n()       → aplica el idioma activo al DOM
//   buildStats()      → genera el marquee de estadísticas
//   buildAmenities()  → genera la grilla de servicios
//   buildRates()      → actualiza los sliders y etiquetas de la calculadora
//   calcRecompute()   → recalcula el estimado de tarifa
//   enviarSolicitud() → POST al endpoint /solicitar/ (apps/publico/views.py)
//   abrirPopup() / cerrarPopup() → controla el modal del formulario
// =============================================================================

// ── I18N ─────────────────────────────────────────────────
// Diccionario de traducción completo para español e inglés.
// Cada clave corresponde a un atributo data-i18n o data-i18n-html en landing.html.
// applyI18n() itera sobre el DOM y reemplaza los textos al cambiar idioma.
const I18N = {
  es: {
    "topbar.location":"Isla Navidad, Colima, México","topbar.hours":"Lun–Vie · 9:00 – 18:00",
    "nav.marina":"La Marina","nav.amenities":"Amenidades","nav.rates":"Tarifas","nav.gallery":"Galería","nav.contact":"Contacto","nav.reserve":"Reservar",
    "hero.eyebrow":"Costa Pacífico · Marina Privada",
    "hero.title":'<span class="word" style="animation-delay:.6s">Donde</span> <span class="word" style="animation-delay:.7s">el</span> <span class="word italic" style="animation-delay:.8s">océano</span><br><span class="word" style="animation-delay:.9s">encuentra</span> <span class="word" style="animation-delay:1.0s">su</span> <span class="word italic" style="animation-delay:1.1s">refugio.</span>',
    "hero.sub":"Entre las 10 mejores marinas privadas de América Latina, Puerto de la Navidad ofrece servicios de clase mundial en uno de los puertos naturales más seguros del Pacífico mexicano.",
    "hero.cta1":"Solicitar reservación","hero.cta2":"Explorar la marina","hero.scroll":"Descubrir",
    "stat.slips":"Slips disponibles","stat.length":"Pies de eslora máx.","stat.depth":"Pies de calado","stat.security":"Seguridad continua","stat.diamond":"AAA Four Diamond","stat.airport":"Min al aeropuerto",
    "badge.diamond":"Cuatro Diamantes","badge.sub":"Reconocimiento Internacional",
    "about.eyebrow":"Marina Puerto de la Navidad","about.title1":"Un puerto seguro,","about.title2":"una experiencia íntima.",
    "about.lead":"Ubicada en Isla Navidad, un desarrollo turístico privado de alto nivel, a solo 30 minutos del Aeropuerto Internacional de Manzanillo (ZLO).",
    "about.p1":"Con capacidad para hasta 200 embarcaciones de hasta 250 ft, nuestra marina opera con los más altos estándares de seguridad y mantiene fuertes vínculos con las principales aseguradoras internacionales.",
    "about.p2":"Un refugio natural — hurricane hole ideal para el dockage de verano — con estación de combustible marítimo, agua, electricidad y conexiones sanitarias en cada slip.",
    "about.cred1":"Embarcaciones","about.cred2":"Eslora máxima","about.cred3":"Seguridad",
    "amen.eyebrow":"Servicios e instalaciones","amen.title1":"Todo lo necesario,","amen.title2":"nada superfluo.",
    "amen.sub":"Servicios de clase mundial diseñados para que tu embarcación y tripulación se sientan como en casa.",
    "rates.eyebrow":"Tarifas Verano 2026","rates.title1":"Calcula tu","rates.title2":"estadía.",
    "rates.sub":"Vigencia del 1 de mayo al 31 de octubre de 2026. Estima tu tarifa antes de reservar — todos los pagos se confirman con el Harbormaster.",
    "rates.daily":"Diario","rates.monthly":"Mensual",
    "rates.includes":"Incluye","rates.includesText":"Agua potable, duchas, seguridad 24/7, Wi-Fi en áreas públicas. + 16% IVA aplicable.",
    "rates.power":"Servicio eléctrico","rates.powerText":"Mensual: 30 A $4.87 · 50 A $7.04 · 100 A $10.28 USD/ft/mes. Diario: $7.20 MXN/kWh medido.",
    "rates.payment":"Pago","rates.paymentText":"AMEX, VISA, MasterCard, efectivo y transferencia. Anticipado y no reembolsable.",
    "calc.eyebrow":"Estimador","calc.title":"Configura tu embarcación","calc.length":"Eslora","calc.duration":"Duración",
    "calc.power":"Servicio eléctrico","calc.power.none":"Sin servicio","calc.estimate":"Estimación total",
    "calc.note":"Estimación aproximada. Sujeta a + 16% IVA y a confirmación de disponibilidad con el Harbormaster.",
    "calc.cta":"Solicitar esta estadía","calc.bd.dockage":"Atraque","calc.bd.power":"Energía eléctrica","calc.bd.tax":"IVA (16%)",
    "ref.short.name":"1 – 2 días","ref.short.sub":"Estancia corta","ref.short.notes":"Tránsito o paradas breves.",
    "ref.mid.name":"3 – 4 días","ref.mid.sub":"Estancia media","ref.mid.notes":"Estadía media · acceso al resort.",
    "ref.long.name":"5+ días","ref.long.sub":"Larga estancia","ref.long.notes":"Mejor tarifa diaria · soporte de trámites.",
    "ref.m1.name":"1 – 2 meses","ref.m1.sub":"Mensual","ref.m1.notes":"Wi-Fi, seguridad y pump-out incluidos.",
    "ref.m3.name":"3 meses","ref.m3.sub":"Trimestral","ref.m3.notes":"Incluye 1 green fee de cortesía · acceso al Country Club.",
    "ref.m6.name":"6 meses","ref.m6.sub":"Semestral","ref.m6.notes":"Green fees cada 2 meses o cena para dos · almacén con descuento.",
    "sheet.jump":"Calcular aproximado","calc.hint":"Estima el costo según eslora, duración y servicio eléctrico",
    "sheet.eyebrow":"Slip Rates","sheet.title":"Verano 2026","sheet.validity":"Vigencia · 1 de mayo al 31 de octubre de 2026",
    "sheet.dailyTitle":"Tarifas diarias","sheet.dailyUnit":"USD / pie / día",
    "sheet.d1":"1 – 2 días","sheet.d1n":"Tránsito o paradas breves","sheet.d2":"3 – 4 días","sheet.d2n":"Estadía media · acceso al resort","sheet.d3":"5+ días","sheet.d3n":"Mejor tarifa diaria",
    "sheet.dailyPower":"Servicio eléctrico (medido)","sheet.monthlyTitle":"Tarifas mensuales","sheet.monthlyUnit":"USD / pie / mes",
    "sheet.m1":"1 – 2 meses","sheet.m1n":"Tarifa base mensual","sheet.m2":"3 meses","sheet.m2n":"Green fee de cortesía · Country Club","sheet.m3":"6 meses","sheet.m3n":"Green fees bimestrales o cena para dos",
    "sheet.monthlyPower":"Servicio eléctrico adicional","sheet.disclaimerTitle":"Cotización aproximada",
    "sheet.disclaimer":"Las tarifas mostradas son referenciales. Para cotización oficial y confirmación de disponibilidad, comunícate directamente con nuestro Harbormaster antes de iniciar el proceso de reserva.",
    "sheet.payment":"Pago anticipado · no reembolsable","sheet.cash":"EFECTIVO","sheet.wire":"TRANSFERENCIA",
    "gal.eyebrow":"Galería","gal.title1":"Postales","gal.title2":"de Isla Navidad.",
    "gal.1":"Atardecer en la bahía","gal.2":"Resort Grand Isla","gal.3":"Slips privados","gal.4":"Sabores del Pacífico","gal.5":"Campo de golf","gal.6":"Playa privada","gal.7":"Mesa frente al mar","gal.8":"Country Club",
    "perks.eyebrow":"Al reservar con nosotros","perks.title1":"Atención personal,","perks.title2":"de capitán a capitán.",
    "perks.p1.t":"Confirmación en 24 hrs","perks.p1.d":"Nuestro Harbormaster confirma disponibilidad y siguientes pasos en menos de un día hábil.",
    "perks.p2.t":"Atención bilingüe","perks.p2.d":"Todo el equipo de marina opera en español e inglés — sin barreras de comunicación.",
    "perks.p3.t":"Apoyo migratorio","perks.p3.d":"Te asistimos con trámites de aduana, inmigración y permisos de importación temporal.",
    "perks.p4.t":"Acceso al resort","perks.p4.d":"Restaurantes, alberca, playa privada, golf de 27 hoyos y club de yates — todo a tu alcance.",
    "docs.eyebrow":"Documentación","docs.title1":"Requisitos de","docs.title2":"entrada.",
    "docs.sub":"Apoyamos con todos los trámites desde nuestra oficina. Estos son los documentos a tener listos.",
    "docs.vesselsTitle":"Embarcación",
    "docs.v1":"Registro o documentación vigente del barco","docs.v2":"Seguro de embarcación P.D. + P.L.","docs.v3":"Permiso de importación temporal (vigencia 10 años)","docs.v4":"Despacho del último puerto sellado por capitanía",
    "docs.crewTitle":"Capitán & tripulación",
    "docs.c1":"Pasaportes y documentos migratorios","docs.c2":"Permiso de visa mexicana por inmigración","docs.c3":"Lista de tripulación firmada","docs.c4":"Berthing agreement firmado a la llegada",
    "contact.eyebrow":"Visítanos","contact.title1":"Encuéntranos","contact.title2":"en la Costa Alegre.",
    "contact.p":"Paseo del Pescador s/n, Isla Navidad, Colima, México. A 30 minutos del Aeropuerto Internacional de Manzanillo (ZLO).",
    "contact.coords":"Coordenadas","contact.vhf":"Canal VHF","contact.depth":"Profundidad","contact.harbor":"Harbormaster","contact.cta":"Iniciar reservación",
    "foot.about":"Marina privada de clase mundial en la Costa Alegre del Pacífico mexicano. Operada por Grand Isla Navidad Resort.",
    "foot.explore":"Explorar","foot.contact":"Contacto","foot.directions":"Cómo llegar","foot.creds":"Reconocimientos","foot.rights":"Todos los derechos reservados.","foot.privacy":"Aviso de privacidad","foot.terms":"Términos",
    "amen.wifi.t":"Wi-Fi de alta velocidad","amen.wifi.d":"Cobertura en muelles y áreas públicas.",
    "amen.security.t":"Seguridad 24/7","amen.security.d":"Vigilancia continua, acceso controlado.",
    "amen.fuel.t":"Estación de combustible","amen.fuel.d":"Gasolina sin plomo y diesel marino en sitio.",
    "amen.water.t":"Agua y electricidad","amen.water.d":"30 A / 50 A / 100 A · 110V – 480V trifásico.",
    "amen.pump.t":"Pump-out en cada slip","amen.pump.d":"Instalación de bombeo de aguas residuales.",
    "amen.laundry.t":"Lavandería y duchas","amen.laundry.d":"Vestidores con vapor y casilleros en el club de golf.",
    "amen.taxi.t":"Water taxi 24 hrs","amen.taxi.d":"Conexión con Barra de Navidad por canal 23.",
    "amen.resort.t":"Acceso al resort","amen.resort.d":"4 restaurantes, 3 bares, alberca, playa privada.",
    "amen.golf.t":"Golf 27 hoyos","amen.golf.d":"Green fees especiales para residentes de marina.",
    "amen.fitness.t":"Gimnasio & Spa","amen.fitness.d":"Centro de bienestar con servicios de spa.",
    "amen.concierge.t":"Concierge bilingüe","amen.concierge.d":"Asistencia con trámites, tours y excursiones.",
    "amen.storage.t":"Almacenamiento","amen.storage.d":"Casilleros en sitio y parking con reserva.",

    // es:
    "nav.croquis":"Croquis",
    "croquis.eyebrow":"Distribución",
    "croquis.title":"Croquis de",
    "croquis.it":"la marina.",
    "croquis.sub":"Ubicación de los muelles y espacios disponibles para embarcaciones.",

  },
  en: {
    "topbar.location":"Isla Navidad, Colima, Mexico","topbar.hours":"Mon–Fri · 9:00 am – 6:00 pm",
    "nav.marina":"The Marina","nav.amenities":"Amenities","nav.rates":"Rates","nav.gallery":"Gallery","nav.contact":"Contact","nav.reserve":"Reserve",
    "hero.eyebrow":"Pacific Coast · Private Marina",
    "hero.title":'<span class="word" style="animation-delay:.6s">Where</span> <span class="word" style="animation-delay:.7s">the</span> <span class="word italic" style="animation-delay:.8s">ocean</span><br><span class="word" style="animation-delay:.9s">finds</span> <span class="word" style="animation-delay:1.0s">its</span> <span class="word italic" style="animation-delay:1.1s">sanctuary.</span>',
    "hero.sub":"Among the top 10 private marinas in Latin America, Puerto de la Navidad offers world-class services in one of the safest natural harbors on Mexico's Pacific coast.",
    "hero.cta1":"Request reservation","hero.cta2":"Explore the marina","hero.scroll":"Discover",
    "stat.slips":"Available slips","stat.length":"Max length (ft)","stat.depth":"Feet draft","stat.security":"Continuous security","stat.diamond":"AAA Four Diamond","stat.airport":"Min to airport",
    "badge.diamond":"Four Diamond","badge.sub":"International recognition",
    "about.eyebrow":"Marina Puerto de la Navidad","about.title1":"A safe harbor,","about.title2":"an intimate experience.",
    "about.lead":"Located in Isla Navidad, an upscale private tourist development, just 30 minutes from Manzanillo International Airport (ZLO).",
    "about.p1":"With capacity for up to 200 vessels of up to 250 ft, our marina operates with the highest safety standards and strong ties to major international insurers.",
    "about.p2":"A natural safe haven — ideal hurricane hole for summer dockage — with maritime fuel station, water, electricity and sanitary hookups at every slip.",
    "about.cred1":"Vessels","about.cred2":"Max length","about.cred3":"Security",
    "amen.eyebrow":"Services & facilities","amen.title1":"Everything you need,","amen.title2":"nothing superfluous.",
    "amen.sub":"World-class services designed so your vessel and crew feel right at home.",
    "rates.eyebrow":"Summer 2026 rates","rates.title1":"Estimate your","rates.title2":"stay.",
    "rates.sub":"Valid May 1st through October 31st, 2026. Estimate your rate before reserving — all payments are confirmed with the Harbormaster.",
    "rates.daily":"Daily","rates.monthly":"Monthly",
    "rates.includes":"Includes","rates.includesText":"Drinking water, showers, 24/7 security, Wi-Fi in public areas. + 16% tax applicable.",
    "rates.power":"Electrical service","rates.powerText":"Monthly: 30 A $4.87 · 50 A $7.04 · 100 A $10.28 USD/ft/month. Daily: $7.20 MXN/kWh metered.",
    "rates.payment":"Payment","rates.paymentText":"AMEX, VISA, MasterCard, cash and wire. Payment in advance, non-refundable.",
    "calc.eyebrow":"Estimator","calc.title":"Set up your vessel","calc.length":"Length","calc.duration":"Duration",
    "calc.power":"Electrical service","calc.power.none":"No service","calc.estimate":"Estimated total",
    "calc.note":"Approximate estimate. Subject to + 16% tax and confirmation with the Harbormaster.",
    "calc.cta":"Request this stay","calc.bd.dockage":"Dockage","calc.bd.power":"Electric service","calc.bd.tax":"Tax (16%)",
    "ref.short.name":"1 – 2 days","ref.short.sub":"Short stay","ref.short.notes":"For transit or quick stops.",
    "ref.mid.name":"3 – 4 days","ref.mid.sub":"Mid stay","ref.mid.notes":"Preferred rate · includes resort access.",
    "ref.long.name":"5+ days","ref.long.sub":"Long stay","ref.long.notes":"Best per-day rate · paperwork support.",
    "ref.m1.name":"1 – 2 months","ref.m1.sub":"Monthly","ref.m1.notes":"Wi-Fi, security and pump-out included.",
    "ref.m3.name":"3 months","ref.m3.sub":"Quarterly","ref.m3.notes":"Includes 1 complimentary green fee · Country Club access.",
    "ref.m6.name":"6 months","ref.m6.sub":"Semi-annual","ref.m6.notes":"Green fees every 2 months or dinner for two · discounted storage.",
    "sheet.jump":"Calculate estimate","calc.hint":"Estimate the cost based on length, duration and electric service",
    "sheet.eyebrow":"Slip Rates","sheet.title":"Summer 2026","sheet.validity":"Valid · May 1st through October 31st, 2026",
    "sheet.dailyTitle":"Daily rates","sheet.dailyUnit":"USD / ft / day",
    "sheet.d1":"1 – 2 days","sheet.d1n":"Transit or quick stops","sheet.d2":"3 – 4 days","sheet.d2n":"Mid stay · resort access","sheet.d3":"5+ days","sheet.d3n":"Best daily rate",
    "sheet.dailyPower":"Electric service (metered)","sheet.monthlyTitle":"Monthly rates","sheet.monthlyUnit":"USD / ft / month",
    "sheet.m1":"1 – 2 months","sheet.m1n":"Base monthly rate","sheet.m2":"3 months","sheet.m2n":"Complimentary green fee · Country Club","sheet.m3":"6 months","sheet.m3n":"Bimonthly green fees or dinner for two",
    "sheet.monthlyPower":"Additional electric service","sheet.disclaimerTitle":"Approximate quote",
    "sheet.disclaimer":"The rates shown are for reference only. For an official quote and to confirm availability, please contact our Harbormaster directly before starting the reservation process.",
    "sheet.payment":"Payment in advance · non-refundable","sheet.cash":"CASH","sheet.wire":"WIRE",
    "gal.eyebrow":"Gallery","gal.title1":"Postcards","gal.title2":"from Isla Navidad.",
    "gal.1":"Sunset over the bay","gal.2":"Grand Isla Resort","gal.3":"Private slips","gal.4":"Sabores del Pacífico","gal.5":"Golf course","gal.6":"Private beach","gal.7":"Seaside dining","gal.8":"Country Club",
    "perks.eyebrow":"When you reserve with us","perks.title1":"Personal attention,","perks.title2":"captain to captain.",
    "perks.p1.t":"24-hour confirmation","perks.p1.d":"Our Harbormaster confirms availability and next steps in less than one business day.",
    "perks.p2.t":"Bilingual service","perks.p2.d":"The entire marina team operates in Spanish and English — no communication barriers.",
    "perks.p3.t":"Immigration support","perks.p3.d":"We assist with customs, immigration and temporary importation permits.",
    "perks.p4.t":"Resort access","perks.p4.d":"Restaurants, pools, private beach, 27-hole golf and yacht club — all within reach.",
    "docs.eyebrow":"Documentation","docs.title1":"Entry","docs.title2":"requirements.",
    "docs.sub":"We assist with all paperwork from our office. These are the documents to have ready.",
    "docs.vesselsTitle":"Vessel",
    "docs.v1":"Current vessel registration or documentation","docs.v2":"Boat insurance P.D. + P.L.","docs.v3":"Temporary importation permit (10-year validity)","docs.v4":"Despacho from last port stamped by Port Captain",
    "docs.crewTitle":"Captain & crew",
    "docs.c1":"Passports and immigration documents","docs.c2":"Mexican visa permit by Immigration","docs.c3":"Signed crew list","docs.c4":"Berthing agreement signed upon arrival",
    "contact.eyebrow":"Visit us","contact.title1":"Find us","contact.title2":"on the Costa Alegre.",
    "contact.p":"Paseo del Pescador s/n, Isla Navidad, Colima, Mexico. 30 minutes from Manzanillo International Airport (ZLO).",
    "contact.coords":"Coordinates","contact.vhf":"VHF channel","contact.depth":"Depth","contact.harbor":"Harbormaster","contact.cta":"Start reservation",
    "foot.about":"World-class private marina on the Pacific Costa Alegre of Mexico. Operated by Grand Isla Navidad Resort.",
    "foot.explore":"Explore","foot.contact":"Contact","foot.directions":"Directions","foot.creds":"Recognitions","foot.rights":"All rights reserved.","foot.privacy":"Privacy notice","foot.terms":"Terms",
    "amen.wifi.t":"High-speed Wi-Fi","amen.wifi.d":"Coverage on docks and public areas.",
    "amen.security.t":"24/7 Security","amen.security.d":"Continuous surveillance, gated access.",
    "amen.fuel.t":"Fuel station","amen.fuel.d":"Unleaded gasoline and marine diesel on site.",
    "amen.water.t":"Water & power","amen.water.d":"30 A / 50 A / 100 A · 110V – 480V three-phase.",
    "amen.pump.t":"Pump-out per slip","amen.pump.d":"State-of-the-art sewage pump-out facility.",
    "amen.laundry.t":"Laundry & showers","amen.laundry.d":"Locker room with steam rooms at golf clubhouse.",
    "amen.taxi.t":"24-hr water taxi","amen.taxi.d":"Connection to Barra de Navidad via VHF 23.",
    "amen.resort.t":"Resort access","amen.resort.d":"4 restaurants, 3 bars, pools, private beach.",
    "amen.golf.t":"27-hole golf","amen.golf.d":"Special green fees for marina residents.",
    "amen.fitness.t":"Fitness & spa","amen.fitness.d":"Wellness center with spa services.",
    "amen.concierge.t":"Bilingual concierge","amen.concierge.d":"Assistance with paperwork, tours and excursions.",
    "amen.storage.t":"Storage","amen.storage.d":"On-site lockers and limited reserved parking.",

    // en:
    "nav.croquis":"Marina Map",
    "croquis.eyebrow":"Layout",
    "croquis.title":"Marina",
    "croquis.it":"map.",
    "croquis.sub":"Location of docks and available slips for vessels.",

  }
};

// Idioma activo. Cambia al hacer clic en los botones .lang-btn del navbar.
// Valor inicial 'es'; persiste durante la sesión del navegador (no se guarda en localStorage).
let lang = 'es';

// -----------------------------------------------------------------------------
// applyI18n
// Aplica el idioma activo (variable `lang`) a todos los elementos del DOM que
// tengan los atributos data-i18n o data-i18n-html.
//   data-i18n      → reemplaza textContent (texto plano, seguro)
//   data-i18n-html → reemplaza innerHTML (usado en hero.title que contiene <span> animados)
// Al final llama a buildStats(), buildAmenities() y buildRates() para regenerar
// los componentes JS dinámicos con los textos del nuevo idioma.
// -----------------------------------------------------------------------------
function applyI18n(){
  document.documentElement.lang = lang;
  document.querySelectorAll('[data-i18n]').forEach(el=>{
    const k = el.getAttribute('data-i18n');
    if(I18N[lang][k] !== undefined) el.textContent = I18N[lang][k];
  });
  document.querySelectorAll('[data-i18n-html]').forEach(el=>{
    const k = el.getAttribute('data-i18n-html');
    if(I18N[lang][k] !== undefined) el.innerHTML = I18N[lang][k];
  });
  buildStats();
  buildAmenities();
  buildRates();
}

// Listener de cambio de idioma.
// Los botones .lang-btn tienen data-lang="es" o data-lang="en" en landing.html.
// Al hacer clic: desactiva todos, activa el pulsado, actualiza `lang` y re-aplica i18n.
document.querySelectorAll('.lang-btn').forEach(b=>{
  b.addEventListener('click', ()=>{
    document.querySelectorAll('.lang-btn').forEach(x=>x.classList.remove('active'));
    b.classList.add('active');
    lang = b.dataset.lang;   // 'es' o 'en'
    applyI18n();
  });
});



// -----------------------------------------------------------------------------
// Nav scroll
// Agrega la clase 'scrolled' al <nav> cuando el usuario baja más de 80px.
// El CSS de landing usa esa clase para cambiar el fondo del navbar de
// transparente a sólido. {passive:true} mejora el rendimiento del scroll.
// -----------------------------------------------------------------------------
const nav = document.querySelector('nav.main');
function checkScroll(){ nav.classList.toggle('scrolled', window.scrollY > 80); }
window.addEventListener('scroll', checkScroll, {passive:true});

// -----------------------------------------------------------------------------
// Reveal observer (IntersectionObserver)
// Observa todos los elementos con clase .reveal en landing.html.
// Cuando un elemento entra al viewport (≥12% visible), le agrega la clase
// 'show', que el CSS usa para disparar la animación de entrada (fade/slide).
// threshold:0.12 → el elemento debe ser 12% visible antes de animarse,
// evitando que las animaciones se disparen antes de que el usuario las vea.
// -----------------------------------------------------------------------------
const obs = new IntersectionObserver(entries=>{
  entries.forEach(e=>{ if(e.isIntersecting) e.target.classList.add('show'); });
},{threshold:0.12});
document.querySelectorAll('.reveal').forEach(el=>obs.observe(el));

// -----------------------------------------------------------------------------
// buildStats
// Genera el marquee de estadísticas de la marina (banda horizontal animada).
// Escribe el HTML dentro de #statsTrack duplicando los items (html + html)
// para crear el efecto de loop infinito con CSS animation.
// Se llama desde applyI18n() para actualizar las etiquetas al cambiar idioma.
// Afecta: el elemento #statsTrack en landing.html (banda de stats bajo el hero).
// -----------------------------------------------------------------------------
function buildStats(){
  const t = I18N[lang];
  const items = [
    {num:"200",  lbl:t["stat.slips"]},
    {num:"250",  lbl:t["stat.length"]},
    {num:"12",   lbl:t["stat.depth"]},
    {num:"24/7", lbl:t["stat.security"]},
    {num:"AAA",  lbl:t["stat.diamond"]},
    {num:"30",   lbl:t["stat.airport"]}
  ];
  const html = items.map(s=>
    `<div class="stat"><span class="num">${s.num}</span><span class="lbl">${s.lbl}</span><span class="div"></span></div>`
  ).join('');
  // Se duplica el HTML para que el marquee CSS pueda hacer loop sin salto visible
  document.getElementById('statsTrack').innerHTML = html + html;
}

// -----------------------------------------------------------------------------
// AMENITY_ICONS / buildAmenities
// AMENITY_ICONS: diccionario de SVG inline para cada amenidad de la marina.
// Cada SVG es un string literal; la clave coincide con el prefijo usado en I18N
// (ej: clave 'wifi' → I18N[lang]['amen.wifi.t'] y I18N[lang]['amen.wifi.d']).
//
// buildAmenities: genera la grilla de cards de amenidades dentro de #amenGrid.
// Itera sobre las 12 claves en orden visual y construye cada card con el ícono,
// título y descripción del idioma activo.
// Se llama desde applyI18n() al cambiar idioma.
// Afecta: el elemento #amenGrid en landing.html (sección "Amenidades").
// -----------------------------------------------------------------------------
const AMENITY_ICONS = {
  wifi:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 12.55a11 11 0 0 1 14 0M1.42 9a16 16 0 0 1 21.16 0M8.53 16.11a6 6 0 0 1 6.95 0"/><circle cx="12" cy="20" r="1" fill="currentColor" stroke="none"/></svg>',
  security:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>',
  fuel:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><line x1="3" y1="22" x2="15" y2="22"/><line x1="4" y1="9" x2="14" y2="9"/><path d="M14 22V4a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v18"/><path d="M14 13h2a2 2 0 0 1 2 2v2a2 2 0 0 0 2 2 2 2 0 0 0 2-2V9.83a2 2 0 0 0-.59-1.42L18 5"/></svg>',
  water:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><polyline points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
  pump:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 12h3l3-9 6 18 3-9h3"/></svg>',
  laundry:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="4" y="3" width="16" height="18" rx="2"/><circle cx="12" cy="14" r="4"/><circle cx="8" cy="7" r=".5" fill="currentColor"/><circle cx="11" cy="7" r=".5" fill="currentColor"/></svg>',
  taxi:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M2 12l2-7h16l2 7M3 12h18v6H3z"/><circle cx="7" cy="18" r="2"/><circle cx="17" cy="18" r="2"/></svg>',
  resort:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 21h18M5 21V11l7-7 7 7v10M9 21v-6h6v6"/></svg>',
  golf:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 2v20M12 4l8 2-8 3"/><circle cx="8" cy="20" r="2"/></svg>',
  fitness:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M6 4v16M18 4v16M2 9v6M22 9v6M6 12h12"/></svg>',
  concierge:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="8" r="4"/><path d="M4 22a8 8 0 0 1 16 0"/></svg>',
  storage:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="18" height="18" rx="1"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="15" y1="3" x2="15" y2="21"/></svg>'
};

function buildAmenities(){
  const t = I18N[lang];
  const keys = ['wifi','security','fuel','water','pump','laundry','taxi','resort','golf','fitness','concierge','storage'];
  document.getElementById('amenGrid').innerHTML = keys.map(k=>`
    <div class="amen">
      <div class="amen-icon">${AMENITY_ICONS[k]}</div>
      <h3>${t['amen.'+k+'.t']}</h3>
      <p>${t['amen.'+k+'.d']}</p>
    </div>`).join('');
}

// =============================================================================
// CALCULADORA DE TARIFAS
// Estima el costo total de estadía según eslora, duración, modo (diario/mensual)
// y servicio eléctrico opcional. Muestra el desglose en #calcBreakdown y el
// total en #calcTotal. Soporta dos idiomas (plurales diferentes en ES/EN).
//
// Estado de la calculadora (variables globales del módulo):
//   calcMode     → 'daily' | 'monthly'  (cambia con botones .calc-mode)
//   calcLength   → eslora en pies (slider #calcLength, default 45)
//   calcDuration → días o meses (slider #calcDuration, default 3)
//   calcPower    → amperaje del servicio eléctrico: 0 (ninguno), 30, 50 o 100
//                  (cambia con botones .calc-pill que tienen data-power)
// =============================================================================

// Tarifa base diaria en USD/pie/día según cantidad de días
// Escalonada: 1–2 días = $2.30, 3–4 días = $1.89, 5+ días = $1.54
let calcMode='daily', calcLength=45, calcDuration=3, calcPower=0;

function getDailyRate(d){ return d<=2?2.30:d<=4?1.89:1.54; }

// Tarifa base mensual en USD/pie/mes según cantidad de meses
// Escalonada: 1–2 meses = $18.38, 3–5 meses = $17.00, 6+ meses = $16.20
function getMonthlyRate(m){ return m<=2?18.38:m<=5?17.00:16.20; }

// Tarifas de energía eléctrica mensual (USD/pie/mes según amperaje)
const POWER_MONTHLY={30:4.87, 50:7.04, 100:10.28};

// Tarifas de energía eléctrica diaria aproximada (USD/día según amperaje)
// Son valores fijos por día (no por pie): 30A≈$6, 50A≈$9, 100A≈$14
const POWER_DAILY_APPROX={30:6, 50:9, 100:14};

// -----------------------------------------------------------------------------
// calcRecompute
// Recalcula y actualiza el estimado completo de la calculadora.
// Fórmula:
//   base     = tarifa_por_pie × eslora × duración
//   power    = (diario: tarifa_fija_diaria × duración)
//              (mensual: tarifa_por_pie × eslora × duración)
//   subtotal = base + power
//   tax      = subtotal × 0.16  (IVA 16%)
//   total    = subtotal + tax
//
// El total se actualiza con una micro-animación de opacidad (fade 80ms)
// para dar feedback visual al usuario al mover los sliders.
//
// Actualiza en el DOM:
//   #calcTotal        → total final redondeado con separador de miles
//   #calcBreakdown    → desglose línea por línea (atraque, energía, IVA)
//   #calcDurationVal  → número de días/meses seleccionado
//   #calcDurationUnit → etiqueta 'días'/'meses'/'days'/'months' (con plural)
//   #calcLengthVal    → eslora actual en pies
// -----------------------------------------------------------------------------
function calcRecompute(){
  const t = I18N[lang];
  const isDaily  = calcMode==='daily';
  const rate     = isDaily ? getDailyRate(calcDuration) : getMonthlyRate(calcDuration);
  const base     = rate * calcLength * calcDuration;
  const power    = calcPower>0
    ? (isDaily ? POWER_DAILY_APPROX[calcPower]*calcDuration
               : POWER_MONTHLY[calcPower]*calcLength*calcDuration)
    : 0;
  const subtotal = base + power;
  const tax      = subtotal * 0.16;
  const total    = subtotal + tax;

  // Actualiza el total con micro-animación de fade
  const amtEl = document.getElementById('calcTotal');
  amtEl.style.opacity='0.4';
  setTimeout(()=>{ amtEl.textContent=Math.round(total).toLocaleString(); amtEl.style.opacity='1'; },80);

  // Construye la línea descriptiva de la tarifa base (ej: "45 ft × 3 días × $1.89")
  const isP      = calcDuration>1;
  const unitLabel = isDaily
    ? (lang==='es'
        ? `${calcLength} ft × ${calcDuration} día${isP?'s':''} × $${rate.toFixed(2)}`
        : `${calcLength} ft × ${calcDuration} day${isP?'s':''} × $${rate.toFixed(2)}`)
    : (lang==='es'
        ? `${calcLength} ft × ${calcDuration} mes${isP?'es':''} × $${rate.toFixed(2)}`
        : `${calcLength} ft × ${calcDuration} month${isP?'s':''} × $${rate.toFixed(2)}`);

  // Construye el HTML del desglose línea por línea
  let bd=`<div class="calc-bd-row"><span class="lbl">${t['calc.bd.dockage']}</span><span class="val">$${base.toFixed(2)}</span></div>
    <div class="calc-bd-row muted"><span class="lbl">${unitLabel}</span><span class="val"></span></div>`;
  if(calcPower>0)
    bd+=`<div class="calc-bd-row"><span class="lbl">${t['calc.bd.power']} · ${calcPower} A</span><span class="val">$${power.toFixed(2)}</span></div>`;
  bd+=`<div class="calc-bd-row"><span class="lbl">${t['calc.bd.tax']}</span><span class="val">$${tax.toFixed(2)}</span></div>`;
  document.getElementById('calcBreakdown').innerHTML=bd;

  // Actualiza etiquetas de resumen bajo los sliders
  const unitKey = isDaily
    ? (lang==='es'?(isP?'días':'día'):(isP?'days':'day'))
    : (lang==='es'?(isP?'meses':'mes'):(isP?'months':'month'));
  document.getElementById('calcDurationVal').textContent=calcDuration;
  document.getElementById('calcDurationUnit').textContent=unitKey;
  document.getElementById('calcLengthVal').textContent=calcLength;
}

// -----------------------------------------------------------------------------
// buildRates
// Configura el slider de duración (#calcDuration) según el modo activo y
// actualiza sus etiquetas de escala (#calcScale1/2/3).
// Modo diario:   slider de 1–30 días
// Modo mensual:  slider de 1–12 meses
// Si calcDuration excede el nuevo máximo, lo resetea a 3.
// Se llama desde applyI18n() (al cambiar idioma) y al cambiar de modo.
// Afecta: sección "Calculadora" en landing.html.
// -----------------------------------------------------------------------------
function buildRates(){
  const slider=document.getElementById('calcDuration');
  if(calcMode==='daily'){
    slider.min=1; slider.max=30;
    if(calcDuration>30) calcDuration=3;  // Resetea si el valor era de modo mensual
    document.getElementById('calcScale1').textContent=lang==='es'?'1 día':'1 day';
    document.getElementById('calcScale2').textContent=lang==='es'?'15 días':'15 days';
    document.getElementById('calcScale3').textContent=lang==='es'?'30 días':'30 days';
  } else {
    slider.min=1; slider.max=12;
    if(calcDuration>12) calcDuration=3;  // Resetea si el valor era de modo diario
    document.getElementById('calcScale1').textContent=lang==='es'?'1 mes':'1 month';
    document.getElementById('calcScale2').textContent=lang==='es'?'6 meses':'6 months';
    document.getElementById('calcScale3').textContent=lang==='es'?'12 meses':'12 months';
  }
  slider.value=calcDuration;
  document.getElementById('calcLength').value=calcLength;
  calcRecompute();
}

// Listeners de los controles de la calculadora en landing.html:
// #calcLength   → slider de eslora (pies)
// #calcDuration → slider de duración (días o meses según modo)
// .calc-pill    → botones de amperaje eléctrico (data-power: 0/30/50/100)
// .calc-mode    → botones de modo diario/mensual (data-mode: 'daily'/'monthly')
document.getElementById('calcLength').addEventListener('input',e=>{ calcLength=parseInt(e.target.value); calcRecompute(); });
document.getElementById('calcDuration').addEventListener('input',e=>{ calcDuration=parseInt(e.target.value); calcRecompute(); });
document.querySelectorAll('.calc-pill').forEach(b=>{
  b.addEventListener('click',()=>{
    document.querySelectorAll('.calc-pill').forEach(x=>x.classList.remove('active'));
    b.classList.add('active');
    calcPower=parseInt(b.dataset.power);  // 0 = sin servicio, 30/50/100 = amperaje
    calcRecompute();
  });
});
document.querySelectorAll('.calc-mode').forEach(b=>{
  b.addEventListener('click',()=>{
    document.querySelectorAll('.calc-mode').forEach(x=>x.classList.remove('active'));
    b.classList.add('active');
    calcMode=b.dataset.mode;  // 'daily' o 'monthly'
    buildRates();             // Reconfigura el slider y recalcula
  });
});

// -----------------------------------------------------------------------------
// Calculator toggle (IIFE)
// Controla el panel colapsable de la calculadora (#calcCollapsible).
// Al hacer clic en #calcToggleBtn:
//   - Alterna la clase 'open' en el panel (el CSS controla la animación de altura)
//   - Actualiza aria-expanded para accesibilidad
//   - Si se abre, hace scroll suave al panel (con delay de 200ms para que la
//     animación CSS de apertura haya comenzado antes del scroll)
// Se encapsula en IIFE para no contaminar el scope global con btn/panel.
// Afecta: botón "Calcular aproximado" en la sección de tarifas de landing.html.
// -----------------------------------------------------------------------------
(function(){
  const btn   = document.getElementById('calcToggleBtn');
  const panel = document.getElementById('calcCollapsible');
  if(!btn || !panel) return;
  btn.addEventListener('click',()=>{
    const open = panel.classList.toggle('open');
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    // Delay de 200ms para que la animación CSS de apertura inicie antes del scroll
    if(open) setTimeout(()=>panel.scrollIntoView({behavior:'smooth', block:'center'}), 200);
  });
})();

// =============================================================================
// FORMULARIO DE SOLICITUD
// Gestiona el modal del formulario de reservación, el envío al backend y la
// validación del lado cliente.
//
// Flujo completo:
//   1. Usuario hace clic en "Reservar" → abrirPopup() abre el modal
//   2. Llena el formulario #form-solicitud en landing.html
//   3. Hace clic en "Enviar" → llama enviarSolicitud() desde el atributo onclick
//   4. enviarSolicitud() valida con checkValidity() (validación nativa HTML5)
//   5. Hace fetch POST a /solicitar/ (apps/publico/views.py → solicitud_submit)
//      enviando FormData (incluyendo el token CSRF)
//   6a. Éxito (json.ok=true): reemplaza #popup-body con mensaje de confirmación
//       que incluye el email del cliente y el número de solicitud generado
//   6b. Error de validación (json.ok=false): muestra json.error en #form-error
//   6c. Error de red: muestra mensaje de conexión fallida en #form-error
//
// Endpoint: POST /solicitar/ → apps/publico/views.py → solicitud_submit()
// Respuesta esperada: { ok: bool, solicitud_id?: int, email?: str, error?: str }
// =============================================================================

// CSRF: leído del meta tag inyectado por Django en landing.html ({% csrf_token %})
// Se incluye automáticamente en FormData si el input csrf_token está en el form.
const CSRF = document.querySelector('meta[name="csrf-token"]')?.content || '';

// -----------------------------------------------------------------------------
// enviarSolicitud
// Función async que maneja el submit del formulario de reservación.
// Se llama desde el atributo onclick del botón #btn-submit en landing.html.
// Deshabilita el botón durante el envío para evitar doble submit.
// En éxito, sobreescribe el contenido del popup con la confirmación.
// En error, muestra el mensaje en #form-error y rehabilita el botón.
// -----------------------------------------------------------------------------
async function enviarSolicitud(){
  const form  = document.getElementById('form-solicitud');
  const errEl = document.getElementById('form-error');
  errEl.style.display = 'none';

  // checkValidity() activa la validación nativa HTML5 (required, type, min/max)
  // reportValidity() muestra los mensajes de error nativos del navegador
  if(!form.checkValidity()){ form.reportValidity(); return; }

  const btn = document.getElementById('btn-submit');
  btn.disabled = true;
  btn.textContent = lang==='es' ? 'Enviando...' : 'Sending...';

  const data = new FormData(form);  // Incluye todos los campos + csrfmiddlewaretoken
  try{
    const res  = await fetch('/solicitar/', {method:'POST', body:data});
    const json = await res.json();

    if(json.ok){
      // Reemplaza el cuerpo del popup con la confirmación de éxito
      // Muestra el email del cliente y el número de solicitud para referencia
      document.getElementById('popup-body').innerHTML=`
        <div class="success-box">
          <div class="success-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="#1a7a4a" stroke-width="2.5">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </div>
          <h3>${lang==='es'?'¡Solicitud enviada!':'Request sent!'}</h3>
          <p>${lang==='es'?'Hemos recibido su solicitud. Le contactaremos al correo':'We received your request. We will contact you at'} <strong>${json.email}</strong></p>
          <div class="success-num">#${json.solicitud_id}</div>
          <p style="font-size:11px;color:var(--text-light)">${lang==='es'?'Guarde este número de referencia':'Save this reference number'}</p>
        </div>`;
      // Reemplaza el footer del popup con solo el botón "Cerrar"
      document.getElementById('popup-footer').innerHTML=`
        <button class="btn-submit" onclick="cerrarPopup()"
          style="width:100%;padding:.65rem;background:#1a7a4a;color:#fff;border:none;
                 border-radius:8px;font-family:inherit;font-size:14px;font-weight:500;cursor:pointer">
          ${lang==='es'?'Cerrar':'Close'}
        </button>`;
    } else {
      // Error de validación del servidor (fechas inválidas, campos faltantes, etc.)
      errEl.textContent = json.error;
      errEl.style.display = 'block';
      btn.disabled = false;
      btn.textContent = lang==='es' ? 'Enviar solicitud' : 'Submit request';
    }
  } catch(err){
    // Error de red (servidor caído, timeout, sin conexión)
    errEl.textContent = lang==='es' ? 'Error de conexión. Intente de nuevo.' : 'Connection error. Please try again.';
    errEl.style.display = 'block';
    btn.disabled = false;
    btn.textContent = lang==='es' ? 'Enviar solicitud' : 'Submit request';
  }
}

// -----------------------------------------------------------------------------
// abrirPopup / cerrarPopup
// Controlan la visibilidad del modal de reservación (#popup-overlay).
// abrirPopup: agrega clase 'active' y bloquea el scroll del body.
// cerrarPopup: quita clase 'active' y restaura el scroll.
// El botón "Reservar" del navbar y el CTA del hero llaman a abrirPopup()
// directamente desde su atributo onclick en landing.html.
// -----------------------------------------------------------------------------
function abrirPopup(){
  document.getElementById('popup-overlay').classList.add('active');
  document.body.style.overflow = 'hidden';  // Bloquea scroll mientras el modal está abierto
}
function cerrarPopup(){
  document.getElementById('popup-overlay').classList.remove('active');
  document.body.style.overflow = '';  // Restaura el scroll del body
}

// Cierra el modal al hacer clic fuera del panel (en el overlay oscuro)
document.getElementById('popup-overlay').addEventListener('click', ev=>{
  if(ev.target === document.getElementById('popup-overlay')) cerrarPopup();
});

// Validación client-side de fecha_salida > fecha_llegada.
// setCustomValidity('') limpia el error cuando las fechas son correctas.
// Este mensaje se muestra con la validación nativa del navegador (reportValidity).
document.querySelector('[name=fecha_salida]').addEventListener('change', function(){
  const llegada = document.querySelector('[name=fecha_llegada]').value;
  if(llegada && this.value && this.value <= llegada)
    this.setCustomValidity(lang==='es'
      ? 'La fecha de salida debe ser posterior a la llegada.'
      : 'Departure must be after arrival.');
  else
    this.setCustomValidity('');  // Limpia el error si la fecha es válida
});

// =============================================================================
// Init — Inicialización al cargar el script
// Se ejecuta al final del archivo (el <script> está al final del <body>),
// por lo que el DOM ya está completamente cargado.
//
// applyI18n() → aplica el idioma inicial 'es', genera stats, amenidades y
//               configura la calculadora con sus valores por defecto.
// checkScroll() → evalúa la posición inicial del scroll para asignar la clase
//                 'scrolled' al nav si la página se carga scrolleada (ej: reload).
// =============================================================================
applyI18n();
checkScroll();
