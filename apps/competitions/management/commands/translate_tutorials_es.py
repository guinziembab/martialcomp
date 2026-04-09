"""
Management command to translate all 81 tutorials from French to Spanish.
Updates title_es, steps_es, and tip_es fields via django-modeltranslation.

Usage: python manage.py translate_tutorials_es
"""
import json

from django.core.management.base import BaseCommand

from apps.competitions.models.tutorials import TutorialSection, Tutorial


# =============================================================================
# TRANSLATION DATA
# =============================================================================

TRANSLATIONS = {
    # =========================================================================
    # Seccion 1: Onboarding y Primeros Pasos (7 tutoriales)
    # =========================================================================
    1: {
        'title_es': 'Onboarding y Primeros Pasos',
        'tutorials': {
            1: {
                'title_es': 'Crear tu cuenta y elegir tu rol',
                'steps_es': [
                    "Acceder a MartialComp : Ve a martialcomp.com y haz clic en 'Registrate gratis'. Tambien puedes descargar la app movil desde Play Store o App Store.",
                    "Rellenar el formulario de registro : Ingresa tu apellido, nombre, correo electronico y contrasena. Tambien puedes registrarte con Google, Facebook o Apple ID para un acceso simplificado.",
                    "Elegir tu rol principal : Selecciona tu rol: Responsable de Club, Entrenador, Juez/Arbitro, Practicante o Responsable de Federacion. Esta eleccion determina tu panel de control y funcionalidades, pero podras agregar otros roles mas adelante.",
                    "Confirmar tu email : Revisa tu bandeja de entrada y haz clic en el enlace de confirmacion. Tu cuenta esta activa y puedes acceder a tu panel personalizado.",
                ],
                'tip_es': 'Puedes tener varios roles (ej. entrenador Y practicante). Cambia entre tus roles desde el menu lateral en cualquier momento.',
            },
            2: {
                'title_es': 'Crear tu club',
                'steps_es': [
                    "Iniciar el asistente de creacion : Desde tu panel de control, haz clic en 'Crear un club'. El asistente de configuracion en 4 pasos se inicia automaticamente.",
                    "Informacion general : Ingresa el nombre del club, acronimo, direccion completa y datos de contacto (telefono, email, sitio web). Agrega tu logo en formato PNG o JPG (tamano recomendado: 500x500px).",
                    "Elegir las disciplinas : Selecciona una o mas disciplinas entre las 14+ disponibles: Karate, Judo, BJJ, Taekwondo, MMA, Kung Fu, Aikido, Kendo, Muay Thai, Boxeo, Capoeira, etc.",
                    "Personalizar tu subdominio : Elige tu direccion unica: tu-club.martialcomp.com. Esta sera la direccion publica de tu club, accesible para todos.",
                    "Configurar opciones : Establece los horarios de apertura, agrega una descripcion y fotos de tu dojo. Activa o desactiva el registro online de practicantes.",
                ],
                'tip_es': 'Tu club se crea con el plan Gratuito (hasta 10 miembros). Todas las funcionalidades estan disponibles desde el inicio. Actualiza a Premium cuando superes los 10 miembros.',
            },
            3: {
                'title_es': 'Crear tu federacion',
                'steps_es': [
                    "Solicitar la creacion : Selecciona el rol 'Responsable de Federacion' durante el registro o agregalo desde la configuracion. Completa el formulario de creacion con la informacion oficial de tu federacion.",
                    "Informacion oficial : Ingresa el nombre completo, acronimo, pais, disciplinas cubiertas, numero de registro oficial y datos de contacto.",
                    "Configurar el sitio publico : Personaliza tu pagina publica: banner, logo, colores, descripcion, galeria de fotos y enlaces a tus redes sociales.",
                    "Definir la estructura : Configura tus ligas regionales si aplica, define las categorias de afiliacion para los clubes y las tarifas de cuotas.",
                ],
                'tip_es': 'Las federaciones disponen de un espacio de administracion ampliado para supervisar todos los clubes afiliados, competiciones y grados.',
            },
            4: {
                'title_es': 'Configurar tu perfil de entrenador',
                'steps_es': [
                    "Acceder al perfil de entrenador : Desde el menu lateral, haz clic en 'Mi perfil de entrenador'. Si aun no tienes el rol de entrenador, agregalo desde Configuracion > Mis roles.",
                    "Ingresar tus cualificaciones : Agrega tus diplomas (BPJEPS, DEJEPS, CQP, etc.), tus grados en cada disciplina y tus anos de experiencia.",
                    "Definir tus disciplinas : Selecciona las disciplinas que ensenas y tu nivel de especializacion en cada una (principiantes, avanzados, competicion).",
                    "Establecer tu disponibilidad : Indica tus franjas horarias semanales de ensenanza. Esta informacion sera visible para los clubes que buscan entrenadores.",
                ],
                'tip_es': 'Un perfil de entrenador completo con foto y certificaciones aumenta significativamente tu visibilidad ante los clubes.',
            },
            5: {
                'title_es': 'Configurar tu perfil de juez',
                'steps_es': [
                    "Activar el rol de juez : Desde Configuracion > Mis roles, activa el rol 'Juez / Arbitro'. Ingresa tu numero de licencia de juez si aplica.",
                    "Agregar tus cualificaciones : Indica tu nivel de juez (regional, nacional, internacional), las disciplinas para las que estas cualificado y tus certificaciones.",
                    "Definir tus especialidades : Kata/tecnicas, combate, puntuacion artistica... Cada especialidad te habilita para las competiciones correspondientes.",
                    "Ingresar tu disponibilidad : Indica tus zonas geograficas y periodos de disponibilidad para competiciones.",
                ],
                'tip_es': 'Los organizadores de competiciones podran buscarte e invitarte directamente segun tus cualificaciones y disponibilidad.',
            },
            6: {
                'title_es': 'Configurar tu perfil de practicante',
                'steps_es': [
                    "Completar la informacion personal : Ingresa tu fecha de nacimiento, sexo, peso (para categorias de competicion), estatura y foto de perfil.",
                    "Agregar tu grado actual : Indica tu disciplina principal, tu grado actual (cinturon), la fecha de obtencion y el organismo que lo otorgo.",
                    "Ingresar tu licencia : Agrega tu numero de licencia federativa, la fecha de vencimiento y el certificado medico vigente actual.",
                    "Contactos de emergencia : Agrega al menos un contacto de emergencia (obligatorio para competiciones): nombre, telefono, parentesco.",
                ],
                'tip_es': 'Un perfil completo es necesario para inscribirse en competiciones. El peso y el grado determinan automaticamente tu categoria.',
            },
            7: {
                'title_es': 'Comprender el panel de control y la navegacion',
                'steps_es': [
                    "El panel de control : Tu panel muestra un resumen personalizado: proximos eventos, mensajes recientes, estadisticas rapidas y accesos directos a tus acciones frecuentes.",
                    "La barra lateral : El menu lateral da acceso a todas las secciones: Miembros, Competiciones, Grados, Finanzas, Calendario, Configuracion. Se adapta a tu rol activo.",
                    "Cambiar de rol : Si tienes varios roles (ej. entrenador + practicante), haz clic en tu avatar arriba a la derecha para cambiar. El panel y el menu se adaptan automaticamente.",
                    "Notificaciones y mensajes : El icono de campana arriba a la derecha muestra tus notificaciones: inscripciones, resultados, mensajes. Configura tus preferencias de notificacion en la configuracion.",
                    "Busqueda global : Usa la barra de busqueda para encontrar rapidamente un practicante, club, competicion o evento.",
                ],
                'tip_es': 'Personaliza tu panel fijando tus widgets favoritos. El atajo de teclado Ctrl+K abre la busqueda rapida.',
            },
        },
    },

    # =========================================================================
    # Seccion 2: Gestion del Club (10 tutoriales)
    # =========================================================================
    2: {
        'title_es': 'Gestion del Club',
        'tutorials': {
            1: {
                'title_es': 'Agregar practicantes manualmente',
                'steps_es': [
                    "Abrir el formulario de alta : Desde Miembros > Agregar un practicante, completa el formulario: apellido, nombre, fecha de nacimiento, sexo, email y telefono.",
                    "Informacion adicional : Agrega el grado actual, el numero de licencia, la foto de identificacion (opcional) y el certificado medico.",
                    "Asignar a un grupo : Asigna al practicante a uno o mas grupos de entrenamiento (ej. Karate Adultos Avanzado, Judo Ninos Principiante).",
                    "Enviar la invitacion : Marca 'Enviar un email de invitacion' para que el practicante pueda crear su propia cuenta y acceder a su perfil en linea.",
                ],
                'tip_es': 'El practicante recibira un email con un enlace para completar su registro y descargar la app movil.',
            },
            2: {
                'title_es': 'Importacion masiva de practicantes (CSV/Excel)',
                'steps_es': [
                    "Descargar la plantilla : Desde Miembros > Importar, descarga la plantilla CSV o Excel. El archivo contiene columnas obligatorias: Apellido, Nombre, Fecha_nacimiento, Email, y columnas opcionales: Grado, Licencia, Telefono.",
                    "Rellenar el archivo : Completa el archivo con los datos de tus practicantes. Respeta los formatos: fechas en DD/MM/AAAA, grados como texto (ej. 'Cinturon verde', '2o Dan').",
                    "Cargar y mapear columnas : Importa el archivo. La interfaz de mapeo te permite asociar cada columna de tu archivo con los campos de MartialComp. Verifica el mapeo.",
                    "Validar y corregir : MartialComp detecta errores (duplicados, formatos invalidos). Corrige las filas con errores o saltalas. Confirma la importacion.",
                ],
                'tip_es': 'Puedes importar hasta 500 practicantes en una sola operacion. La importacion detecta automaticamente duplicados por email o apellido + nombre + fecha de nacimiento.',
            },
            3: {
                'title_es': 'Gestionar las fichas de los practicantes',
                'steps_es': [
                    "Acceder a la ficha : Desde la lista de miembros, haz clic en el nombre de un practicante para abrir su ficha completa.",
                    "Ver los detalles : La ficha muestra: informacion personal, historial de grados, competiciones realizadas, asistencia y cuotas.",
                    "Editar la informacion : Haz clic en 'Editar' para actualizar los datos. Los cambios se registran en el historial.",
                    "Acciones rapidas : Desde la ficha puedes: inscribir en una competicion, asignar un grado, enviar un mensaje, generar un certificado.",
                ],
                'tip_es': 'Usa los filtros avanzados (grado, edad, licencia vigente, cuota pagada) para encontrar rapidamente a un practicante.',
            },
            4: {
                'title_es': 'Crear una cuenta de usuario para un practicante',
                'steps_es': [
                    "Acceder a la ficha del practicante : Abre la ficha del practicante correspondiente desde la lista de miembros.",
                    "Vincular a una cuenta : Haz clic en 'Crear una cuenta de usuario'. Se enviara un email de invitacion al practicante con un enlace para crear su contrasena.",
                    "Establecer permisos : Elige lo que el practicante puede hacer: ver sus resultados, inscribirse en competiciones, ver el calendario, pagar en linea.",
                ],
                'tip_es': 'Los practicantes menores pueden tener una cuenta vinculada a la de un padre a traves de la funcion Grupo Familiar.',
            },
            5: {
                'title_es': 'Gestionar roles y permisos del club',
                'steps_es': [
                    "Acceder a la gestion de roles : Desde Configuracion > Roles y permisos, visualiza los roles disponibles: Administrador, Secretario, Tesorero, Entrenador, Miembro.",
                    "Asignar un rol : Selecciona un miembro y asignale un rol. Cada rol otorga acceso a funcionalidades especificas.",
                    "Personalizar permisos : Para cada rol, define los derechos: solo lectura, edicion, eliminacion, acceso a finanzas, gestion de inscripciones.",
                    "Auditar accesos : Consulta el registro de actividades para ver quien hizo que y cuando en la administracion del club.",
                ],
                'tip_es': 'El rol de Administrador tiene todos los derechos. Crea un rol de Secretario con acceso a miembros y calendario pero no a finanzas.',
            },
            6: {
                'title_es': 'Seguimiento de asistencia / Check-in',
                'steps_es': [
                    "Crear una sesion : Desde Asistencia > Nueva sesion, selecciona el grupo de entrenamiento, la fecha y el horario de la clase.",
                    "Registrar por lista : Muestra la lista de miembros del grupo y marca a los presentes. El registro se hace con un solo toque en movil.",
                    "Registrar por codigo QR : Muestra el codigo QR de la sesion. Los practicantes lo escanean con su telefono al llegar al dojo.",
                    "Ver estadisticas : Visualiza las tasas de asistencia por practicante, grupo y periodo. Identifica las ausencias repetidas.",
                ],
                'tip_es': 'El check-in por codigo QR es el metodo mas rapido para grupos grandes. El codigo se renueva en cada sesion para evitar trampas.',
            },
            7: {
                'title_es': 'Gestionar los programas de entrenamiento',
                'steps_es': [
                    "Crear un programa : Desde Programas > Nuevo, define el nombre, la disciplina, el nivel (principiante, intermedio, avanzado) y la duracion del ciclo.",
                    "Planificar las sesiones : Agrega las franjas horarias semanales: dia, hora de inicio, hora de fin, sala/tatami, entrenador responsable.",
                    "Definir los contenidos : Para cada sesion, agrega un plan: calentamiento, trabajo tecnico, sparring/randori, vuelta a la calma. Adjunta archivos o videos.",
                    "Publicar y notificar : Publica el programa. Los practicantes del grupo reciben una notificacion con el programa completo.",
                ],
                'tip_es': 'Duplica un programa existente para crear rapidamente un nuevo ciclo con variaciones.',
            },
            8: {
                'title_es': 'Generar y utilizar los codigos QR del club',
                'steps_es': [
                    "Generar el codigo QR del club : Desde Configuracion > Codigos QR, genera el codigo QR de tu club. Permite a los visitantes acceder directamente a tu pagina publica.",
                    "Codigos QR especiales : Genera codigos QR para: registro online, check-in de sesion, pagina de evento o enlace a la app movil.",
                    "Imprimir y exhibir : Descarga los codigos QR en alta resolucion para imprimir. Formatos disponibles: PNG, SVG, PDF (A4 o tarjeta de presentacion).",
                    "Monitorear estadisticas : Visualiza el numero de escaneos por codigo QR, por dia y por tipo. Identifica los codigos QR mas efectivos.",
                ],
                'tip_es': 'Exhibe el codigo QR de registro en la entrada de tu dojo. Cada escaneo es un cliente potencial!',
            },
            9: {
                'title_es': 'Solicitar la afiliacion a la federacion',
                'steps_es': [
                    "Encontrar tu federacion : Desde Club > Afiliacion, busca tu federacion por nombre, disciplina o pais.",
                    "Enviar la solicitud : Completa el formulario de afiliacion: informacion del club, numero de registro, documentos justificativos (estatutos, seguro, etc.).",
                    "Monitorear el estado : Tu solicitud pasa por etapas: Enviada > En revision > Aprobada/Rechazada. Recibes notificaciones en cada paso.",
                    "Renovar cada temporada : La afiliacion es por temporada. Un recordatorio automatico se envia 30 dias antes del vencimiento.",
                ],
                'tip_es': 'La afiliacion te da acceso a las competiciones oficiales de la federacion y a la gestion centralizada de licencias.',
            },
            10: {
                'title_es': 'Gestionar los traspasos de practicantes',
                'steps_es': [
                    "Iniciar un traspaso : Desde la ficha de un practicante, haz clic en 'Solicitar un traspaso'. Selecciona el club de destino y el motivo del traspaso.",
                    "Proceso de validacion : El club de destino recibe la solicitud y puede aceptarla o rechazarla. Si hay una federacion involucrada, tambien debe validar.",
                    "Traspaso efectivo : Una vez validado, el practicante se transfiere automaticamente con su grado e historial de competiciones.",
                    "Ver el historial : El historial de traspasos es visible en la ficha del practicante y en los informes del club.",
                ],
                'tip_es': 'Algunas federaciones imponen periodos de traspaso (ventanas de transferencia). MartialComp respeta automaticamente estas reglas.',
            },
        },
    },

    # =========================================================================
    # Seccion 3: Competiciones - Creacion y Configuracion (6 tutoriales)
    # =========================================================================
    3: {
        'title_es': 'Competiciones - Creacion y Configuracion',
        'tutorials': {
            1: {
                'title_es': 'Crear una competicion individual',
                'steps_es': [
                    "Iniciar la creacion : Desde Competiciones > Crear, elige el tipo 'Individual'. Ingresa el nombre, la(s) disciplina(s), las fechas y el lugar.",
                    "Definir el formato : Elige el formato: Combate (kumite, randori, sparring), Tecnico (kata, poomsae, formas) o Mixto (ambos).",
                    "Configurar las categorias : Define las categorias por sexo, rango de edad, peso y/o grado. MartialComp ofrece plantillas de categorias estandar por disciplina.",
                    "Opciones y publicacion : Activa las opciones deseadas: inscripcion online, pago, streaming en vivo, resultados publicos. Publica la competicion.",
                ],
                'tip_es': 'Usa las plantillas de categorias (WKF, IJF, ITF...) para ahorrar tiempo. Puedes personalizarlas despues de la creacion.',
            },
            2: {
                'title_es': 'Crear una competicion por equipos (Sincro/Song Luyen)',
                'steps_es': [
                    "Elegir el modo equipo : Durante la creacion, selecciona el tipo 'Equipo'. Define el numero minimo y maximo de miembros por equipo.",
                    "Configurar el formato de equipo : Elige el formato: Sincronizacion (kata/poomsae de equipo), Song Luyen (combate preestablecido para dos) o Combate por equipos (relevos).",
                    "Definir la composicion : Especifica los roles dentro del equipo: numero de titulares, numero de suplentes, si se permiten composiciones mixtas o no.",
                    "Criterios de puntuacion de equipo : Para la puntuacion tecnica, define si los jueces evaluan al equipo en conjunto o a cada miembro individualmente.",
                ],
                'tip_es': 'El modo Sincro permite la puntuacion con criterios de sincronizacion especificos (timing, alineacion, expresion compartida).',
            },
            3: {
                'title_es': 'Configurar las categorias de competicion',
                'steps_es': [
                    "Acceder a la gestion de categorias : Desde la competicion creada, ve a la pestana Categorias. Haz clic en 'Agregar una categoria'.",
                    "Definir los criterios : Para cada categoria, define: sexo (M/F/Mixto), rango de edad (ej. 12-14 anos), rango de peso (ej. -60kg), grado minimo/maximo.",
                    "Nombrar la categoria : Dale un nombre claro: 'Cadete Masculino -52kg' o 'Kata Adulto Femenino Avanzado'. MartialComp genera nombres automaticos si prefieres.",
                    "Ordenar las categorias : Reordena las categorias arrastrando y soltando para establecer el orden de aparicion el dia de la competicion.",
                ],
                'tip_es': 'Importa las categorias de una competicion anterior para ahorrar tiempo. Usa la opcion \'Duplicacion Inteligente\' para crear variantes.',
            },
            4: {
                'title_es': 'Duplicar una competicion existente',
                'steps_es': [
                    "Encontrar la competicion fuente : Desde Competiciones > Historial, encuentra la competicion que quieres duplicar.",
                    "Iniciar la duplicacion : Haz clic en los 3 puntos > Duplicar. Elige que copiar: categorias, reglamento, configuracion, tarifas.",
                    "Ajustar la configuracion : Modifica las fechas, el lugar y los parametros necesarios. Las categorias y el reglamento se copian identicamente.",
                ],
                'tip_es': 'Ideal para competiciones anuales recurrentes. Duplica la edicion anterior y simplemente actualiza las fechas.',
            },
            5: {
                'title_es': 'Configurar las opciones de visibilidad',
                'steps_es': [
                    "Acceder a la configuracion de visibilidad : Desde la competicion, ve a Configuracion > Visibilidad y compartir.",
                    "Inscripciones online : Activa/desactiva las inscripciones publicas. Establece las fechas de apertura y cierre de inscripciones.",
                    "Resultados y clasificaciones : Elige si los resultados son publicos en tiempo real, publicados despues de la validacion o privados (solo organizador).",
                    "Streaming en vivo : Activa el modo streaming y agrega el enlace de YouTube/Twitch/Facebook Live para mostrarlo en la pagina publica.",
                ],
                'tip_es': 'Los resultados en vivo atraen espectadores a tu pagina y aumentan la visibilidad de tu club o federacion.',
            },
            6: {
                'title_es': 'Configurar las reglas de combate',
                'steps_es': [
                    "Elegir un reglamento : Selecciona un reglamento preconfigurado (WKF, IJF, ITF, IBJJF, etc.) o crea uno personalizado.",
                    "Definir la puntuacion : Configura las acciones y sus puntos: Yuko (1pt), Waza-ari (2pts), Ippon (3pts), etc. Agrega las penalizaciones (Shido, Hansoku, etc.).",
                    "Configurar los rounds : Define la duracion de los rounds, el numero de rounds, las pausas y las condiciones de victoria (puntos, Ippon, abandono).",
                    "Reglas especiales : Configura las reglas especificas: Golden Score (tiempo extra), Hantei (decision de los jueces), finalizacion anticipada por diferencia de puntos.",
                ],
                'tip_es': 'Guarda tus reglamentos personalizados como plantillas para reutilizarlos en futuras competiciones.',
            },
        },
    },

    # =========================================================================
    # Seccion 4: Inscripciones y Equipos (7 tutoriales)
    # =========================================================================
    4: {
        'title_es': 'Inscripciones y Equipos',
        'tutorials': {
            1: {
                'title_es': 'Inscribir practicantes en una competicion',
                'steps_es': [
                    "Encontrar la competicion : Desde Competiciones > Abiertas a inscripciones, encuentra la competicion deseada y haz clic en 'Inscribir'.",
                    "Seleccionar los practicantes : Se muestra la lista de tus miembros. Selecciona uno o mas practicantes. MartialComp indica automaticamente las categorias elegibles para cada uno.",
                    "Confirmar las categorias : Para cada practicante, confirma o cambia la categoria propuesta. El sistema verifica que el peso, la edad y el grado correspondan.",
                    "Validar y pagar : Confirma las inscripciones. Si la competicion requiere pago, procede al pago de todas las inscripciones.",
                ],
                'tip_es': 'Los practicantes con un perfil incompleto (peso faltante, licencia vencida) seran senalados con una alerta roja.',
            },
            2: {
                'title_es': 'Inscripcion masiva mediante formulario',
                'steps_es': [
                    "Acceder al modo masivo : Desde la pantalla de inscripcion, haz clic en 'Inscripcion masiva'. Selecciona la categoria de destino.",
                    "Seleccionar el grupo : Filtra por grupo de entrenamiento, grado o edad. Selecciona los practicantes elegibles con un solo clic.",
                    "Verificar y ajustar : La pantalla de verificacion muestra cada practicante con su categoria. Corrige los errores si los hay.",
                    "Confirmar el lote : Valida todas las inscripciones en una sola operacion. Un resumen se envia por email.",
                ],
                'tip_es': 'La inscripcion masiva es ideal para clubes que inscriben a 10+ practicantes en la misma competicion.',
            },
            3: {
                'title_es': 'Crear y gestionar equipos',
                'steps_es': [
                    "Crear un equipo : Desde la competicion, haz clic en 'Inscribir un equipo'. Dale un nombre al equipo y selecciona la categoria.",
                    "Agregar miembros : Agrega miembros del equipo desde tu lista de practicantes. Respeta los numeros minimos y maximos definidos.",
                    "Establecer titulares y suplentes : Designa titulares y suplentes arrastrando y soltando. El orden de aparicion puede establecerse aqui.",
                    "Validar el equipo : Verifica la conformidad del equipo (numero de miembros, categorias individuales) y confirma la inscripcion.",
                ],
                'tip_es': 'En las competiciones por equipos, el nombre del equipo aparece en los marcadores y en los resultados oficiales.',
            },
            4: {
                'title_es': 'Cambiar la categoria de un equipo',
                'steps_es': [
                    "Acceder al equipo : Desde tus inscripciones, encuentra el equipo a modificar y haz clic en 'Editar'.",
                    "Cambiar la categoria : Selecciona la nueva categoria del menu desplegable. El sistema verifica que el equipo cumpla los criterios.",
                    "Confirmar el cambio : Valida. Si la competicion tiene tarifas de inscripcion diferentes por categoria, el ajuste es automatico.",
                ],
                'tip_es': 'El cambio de categoria solo es posible mientras las inscripciones esten abiertas.',
            },
            5: {
                'title_es': 'Solicitar una alianza (fusion inter-clubes)',
                'steps_es': [
                    "Identificar la necesidad : Tu club no tiene suficientes miembros para formar un equipo completo? La alianza permite fusionar equipos de clubes diferentes.",
                    "Crear la solicitud de alianza : Desde el equipo incompleto, haz clic en 'Proponer una alianza'. Selecciona el club asociado y los puestos a cubrir.",
                    "Enviar la propuesta : El club asociado recibe la solicitud con los detalles: competicion, categoria, puestos disponibles, condiciones.",
                    "Finalizar la alianza : Una vez aceptada, el equipo fusionado aparece con los miembros de ambos clubes. El equipo lleva un nombre que combina ambos clubes.",
                ],
                'tip_es': 'La alianza esta sujeta a la aprobacion del organizador de la competicion y, si aplica, de la federacion.',
            },
            6: {
                'title_es': 'Aceptar/rechazar una solicitud de alianza',
                'steps_es': [
                    "Recibir la notificacion : Recibes una notificacion de solicitud de alianza. Haz clic para ver los detalles.",
                    "Revisar la propuesta : Verifica: el club solicitante, la competicion, la categoria, los puestos a cubrir y las condiciones propuestas.",
                    "Aceptar o rechazar : Haz clic en 'Aceptar' para validar la alianza y seleccionar tus miembros, o 'Rechazar' con un mensaje explicativo.",
                ],
                'tip_es': 'Puedes proponer una contrapropuesta modificando las condiciones antes de aceptar.',
            },
            7: {
                'title_es': 'Gestionar las inscripciones recibidas (aprobacion)',
                'steps_es': [
                    "Acceder al panel de inscripciones : Desde la competicion, ve a la pestana Inscripciones. Visualiza las inscripciones por estado: Pendiente, Aprobada, Rechazada.",
                    "Revisar y aprobar : Haz clic en una inscripcion para verificar la informacion del practicante. Aprueba individualmente o en lote.",
                    "Rechazar con motivo : En caso de rechazo, selecciona un motivo: categoria incorrecta, licencia invalida, inscripcion tardia, etc.",
                    "Exportar la lista : Exporta la lista de inscritos validos en CSV o PDF para el pesaje y la gestion el dia de la competicion.",
                ],
                'tip_es': 'Activa la aprobacion automatica si no quieres validar manualmente cada inscripcion.',
            },
        },
    },

    # =========================================================================
    # Seccion 5: Dia de Competicion - Combate (8 tutoriales)
    # =========================================================================
    5: {
        'title_es': 'Dia de Competicion - Combate',
        'tutorials': {
            1: {
                'title_es': 'Generar los grupos automaticamente',
                'steps_es': [
                    "Acceder a la gestion de grupos : Desde la competicion, ve a Grupos > Generar automaticamente. Selecciona las categorias a procesar.",
                    "Configurar la distribucion : Define: numero de competidores por grupo, separacion de miembros del mismo club, cabezas de serie manuales (opcional).",
                    "Generar y verificar : Haz clic en 'Generar'. MartialComp distribuye los competidores evitando enfrentamientos intra-club en la primera ronda.",
                    "Ajustar manualmente : Si es necesario, mueve competidores entre grupos arrastrando y soltando. El sistema verifica conflictos en tiempo real.",
                ],
                'tip_es': 'El algoritmo de distribucion garantiza equidad separando clubes y equilibrando niveles de habilidad entre los grupos.',
            },
            2: {
                'title_es': 'Organizar y reorganizar los grupos',
                'steps_es': [
                    "Vista general de grupos : La pantalla de grupos muestra todas las categorias con el numero de competidores, grupos y estado (borrador, validado, en curso).",
                    "Editar un grupo : Haz clic en un grupo para ver los competidores. Usa arrastrar y soltar para mover un competidor a otro grupo.",
                    "Gestionar ausencias : Marca a un competidor como ausente o retirado. El sistema recalcula automaticamente los enfrentamientos y clasificaciones.",
                    "Validar los grupos : Una vez satisfecho, valida los grupos. Esta accion genera automaticamente la tabla de enfrentamientos.",
                ],
                'tip_es': 'Valida los grupos categoria por categoria para comenzar los combates de las primeras categorias mientras finalizas las demas.',
            },
            3: {
                'title_es': 'Planificar el calendario de combates',
                'steps_es': [
                    "Definir las areas de combate : Desde Programa > Areas, define el numero de tatamis/rings disponibles y sus nombres (Tatami 1, Ring A, etc.).",
                    "Asignar franjas horarias : Arrastra las categorias sobre las areas y las franjas horarias. MartialComp calcula automaticamente la duracion estimada.",
                    "Detectar conflictos : El sistema detecta conflictos: un competidor inscrito en 2 categorias al mismo tiempo. Usa las alertas para ajustar.",
                    "Publicar el programa : Publica el programa. Competidores, entrenadores y jueces reciben una notificacion con sus horarios de participacion.",
                ],
                'tip_es': 'Planifica un 20% de tiempo extra por categoria para gestionar los inevitables retrasos.',
            },
            4: {
                'title_es': 'Usar la interfaz de combate (puntuacion en vivo)',
                'steps_es': [
                    "Conectarse al area : En tu tablet o telefono, abre MartialComp y selecciona tu area de combate asignada. Ingresa tu PIN de juez.",
                    "La interfaz de puntuacion : La pantalla muestra: los 2 competidores (rojo/azul), botones de accion (puntos, penalizaciones), el cronometro y la puntuacion actual.",
                    "Otorgar puntos : Presiona los botones de puntuacion: Yuko (+1), Waza-ari (+2), Ippon (+3) para el competidor rojo o azul. Los puntos se actualizan en tiempo real.",
                    "Gestionar penalizaciones : Presiona Penalizacion para otorgar una advertencia (Shido) o descalificacion (Hansoku). Las penalizaciones son acumulativas.",
                    "Finalizar el combate : El cronometro se detiene automaticamente. Valida el resultado (victoria por puntos, Ippon, abandono). La clasificacion se actualiza instantaneamente.",
                ],
                'tip_es': 'La interfaz esta optimizada para tablets en modo horizontal. Los botones son intencionalmente grandes para un uso rapido y sin errores.',
            },
            5: {
                'title_es': 'Modo Kiosco multi-tatami',
                'steps_es': [
                    "Activar el modo Kiosco : Desde Configuracion > Modo Kiosco, activa el modo y establece un codigo PIN para cada area de combate.",
                    "Configurar cada tablet : En cada tablet del area, inicia sesion y selecciona el area correspondiente. Ingresa el PIN para bloquear la pantalla en esta area.",
                    "Gestion independiente : Cada area funciona autonomamente: puntuacion, cronometro, visualizacion. El marcador central se actualiza en tiempo real.",
                    "Pantalla de espectadores : Conecta una pantalla adicional en modo 'Espectador' para mostrar la puntuacion en gran formato, visible desde las gradas.",
                ],
                'tip_es': 'El modo Kiosco impide que los jueces naveguen accidentalmente fuera de la interfaz de puntuacion.',
            },
            6: {
                'title_es': 'Seguir las clasificaciones en vivo',
                'steps_es': [
                    "Panel en vivo : La pantalla de seguimiento muestra en tiempo real: combates en curso por area, clasificaciones de grupos, avance hacia las fases finales.",
                    "Filtrar por categoria : Selecciona una categoria para ver los detalles: grupos completados, en curso y pendientes, con clasificaciones provisionales.",
                    "Notificaciones automaticas : El sistema notifica automaticamente a los entrenadores cuando sus competidores deben presentarse en el area de combate.",
                ],
                'tip_es': 'Muestra el panel en una pantalla grande en el area de recepcion para que todos los participantes puedan seguir el avance.',
            },
            7: {
                'title_es': 'Generar las fases finales (semifinales/finales)',
                'steps_es': [
                    "Grupos completados : Una vez completados todos los grupos de una categoria, el sistema calcula los clasificados segun las reglas definidas (1o y 2o por grupo, etc.).",
                    "Generar el cuadro : Haz clic en 'Generar fases finales'. El cuadro de eliminacion (cuartos, semifinales, final, final por el bronce) se genera automaticamente.",
                    "Gestionar repescas : Si las reglas lo preveen, las repescas se generan automaticamente con los perdedores de las semifinales.",
                    "Lanzar las finales : Los combates de las fases finales aparecen en el programa. La puntuacion funciona igual que para los grupos.",
                ],
                'tip_es': 'El cuadro de eliminacion se genera automaticamente evitando, cuando es posible, los enfrentamientos entre competidores del mismo club.',
            },
            8: {
                'title_es': 'Gestionar la ceremonia del podio',
                'steps_es': [
                    "Acceder al podio : Desde la categoria completada, haz clic en 'Podio'. La clasificacion final se muestra: Oro, Plata, Bronce (y posiblemente 2 bronces).",
                    "Visualizacion progresiva : Usa el modo 'Ceremonia' para una visualizacion progresiva: 3o, luego 2o, luego 1o, con animaciones y efectos de sonido.",
                    "Proyectar en pantalla grande : Conecta el modo Presentacion a un proyector para una visualizacion espectacular durante la entrega de medallas.",
                    "Compartir resultados : Los podios se publican automaticamente en la pagina de la competicion y pueden compartirse en redes sociales.",
                ],
                'tip_es': 'Toma una foto del podio y agregala a la competicion para enriquecer la galeria y las redes sociales.',
            },
        },
    },

    # =========================================================================
    # Seccion 6: Puntuacion Tecnica (6 tutoriales)
    # =========================================================================
    6: {
        'title_es': 'Puntuacion Tecnica',
        'tutorials': {
            1: {
                'title_es': 'Configurar los criterios de puntuacion',
                'steps_es': [
                    "Acceder a los criterios : Desde la competicion, ve a Puntuacion > Criterios. Selecciona una plantilla o crea tus propios criterios.",
                    "Definir los criterios : Agrega criterios de evaluacion: Tecnica (posiciones, transiciones), Potencia (kime, dinamica), Ritmo (tempo, fluidez), Expresion (zanshin, espiritu).",
                    "Asignar pesos : Define el peso de cada criterio: ej. Tecnica 40%, Potencia 25%, Ritmo 20%, Expresion 15%. El total debe ser 100%.",
                    "Definir la escala : Elige la escala de puntuacion: 1-5, 1-10, 5.0-10.0 o personalizada. Define el incremento (0.1, 0.5 o 1).",
                ],
                'tip_es': 'Las plantillas WKF y WTF estan preconfiguradas. Personalízalas segun tus necesidades especificas.',
            },
            2: {
                'title_es': 'Asignar jueces a las categorias',
                'steps_es': [
                    "Abrir el panel de asignacion : Desde Puntuacion > Jueces, visualiza la lista de jueces registrados y las categorias a cubrir.",
                    "Asignar por categoria : Arrastra los jueces a las categorias. Define el numero de jueces por categoria (generalmente 5 o 7).",
                    "Verificacion de neutralidad : MartialComp verifica automaticamente los conflictos de interes: un juez no puede evaluar a un competidor de su propio club.",
                    "Gestionar las rotaciones : Planifica las rotaciones de jueces entre categorias para prevenir la fatiga y mantener la equidad.",
                ],
                'tip_es': 'El sistema de deteccion de sesgos analiza las diferencias de puntuacion entre jueces y alerta si un juez puntua sistematicamente demasiado alto o bajo.',
            },
            3: {
                'title_es': 'Usar la hoja de puntuacion tecnica',
                'steps_es': [
                    "Iniciar sesion como juez : En tu tablet, inicia sesion con tu cuenta de juez. Selecciona la categoria asignada.",
                    "Interfaz de puntuacion : La pantalla muestra el competidor actual, los criterios de evaluacion y el teclado numerico. Cada criterio tiene su propio deslizador o teclado.",
                    "Evaluar por turno : Para cada competidor, ingresa tu puntuacion para cada criterio. Valida tu evaluacion antes de pasar al siguiente.",
                    "Guardar : Tu evaluacion se guarda instantaneamente. Puedes modificar tus puntuaciones mientras el turno no haya sido bloqueado por el organizador.",
                ],
                'tip_es': 'La interfaz digital esta optimizada para una entrada rapida en tablets. Un solo toque para cada puntuacion.',
            },
            4: {
                'title_es': 'Puntuacion tecnica de equipo (Sincro)',
                'steps_es': [
                    "Entender el modo equipo : En la puntuacion Sincro, aparecen criterios adicionales: Sincronizacion, Alineacion Espacial, Expresion Compartida.",
                    "Evaluar al equipo en conjunto : Si esta configurado asi, evalua al equipo en conjunto para cada criterio, incluida la sincronizacion.",
                    "Evaluar individualmente + equipo : Si esta configurado para evaluacion mixta, evalua a cada miembro individualmente Y LUEGO agrega una puntuacion de equipo para la sincronizacion.",
                ],
                'tip_es': 'En modo Sincro, el criterio de sincronizacion representa tipicamente el 20-30% de la puntuacion total.',
            },
            5: {
                'title_es': 'Bloquear y publicar las puntuaciones',
                'steps_es': [
                    "Verificar las puntuaciones : Desde el panel del organizador, visualiza las puntuaciones de todos los jueces para cada competidor. Identifica las diferencias sospechosas.",
                    "Bloquear un turno : Haz clic en 'Bloquear' para impedir cualquier modificacion. El calculo final (eliminar puntuacion mas alta/mas baja, promedio) se realiza.",
                    "Publicar los resultados : Publica las clasificaciones. Las puntuaciones detalladas por juez pueden ocultarse o mostrarse segun tu configuracion.",
                    "Modo prueba / reinicio : Antes de la competicion, usa el modo prueba para verificar el sistema. El reinicio elimina todas las puntuaciones de prueba.",
                ],
                'tip_es': 'El bloqueo turno por turno permite publicar resultados turno por turno mientras la competicion continua.',
            },
            6: {
                'title_es': 'Ver las clasificaciones provisionales',
                'steps_es': [
                    "Acceder a las clasificaciones : Desde la pestana Clasificaciones, visualiza las clasificaciones en tiempo real con las puntuaciones por criterio y la puntuacion final.",
                    "Ordenar y filtrar : Ordena por puntuacion total o por criterio especifico. Filtra por grupo o todos los competidores.",
                    "Estadisticas de los jueces : Visualiza las estadisticas: promedio por juez, desviacion estandar, deteccion de sesgos. Una herramienta esencial para la equidad.",
                ],
                'tip_es': 'La clasificacion provisional solo es visible para organizadores y jueces. Se publica a los competidores solo despues del bloqueo.',
            },
        },
    },

    # =========================================================================
    # Seccion 7: Resultados y Palmares (4 tutoriales)
    # =========================================================================
    7: {
        'title_es': 'Resultados y Palmares',
        'tutorials': {
            1: {
                'title_es': 'Ver los resultados de la competicion',
                'steps_es': [
                    "Encontrar la competicion : Desde el menu Competiciones o la pagina publica, selecciona la competicion deseada.",
                    "Consultar los resultados : Los resultados estan organizados por categoria. Para cada categoria: podio, clasificacion completa y detalles de las puntuaciones.",
                    "Detalles del combate : Haz clic en un combate para ver los detalles: puntuacion por round, penalizaciones, cronometro y posiblemente el video del combate.",
                ],
                'tip_es': 'Los resultados publicos son accesibles sin cuenta MartialComp a traves del enlace de la competicion.',
            },
            2: {
                'title_es': 'Publicar y compartir los resultados',
                'steps_es': [
                    "Validar los resultados : Desde el panel del organizador, revisa los resultados de cada categoria. Haz clic en 'Validar y publicar'.",
                    "Generar el enlace publico : Se genera un enlace permanente a la pagina de resultados. Copialo para compartirlo.",
                    "Compartir en redes sociales : Usa los botones de compartir integrados para publicar en Facebook, Instagram, Twitter. Los podios generan automaticamente una imagen.",
                    "Codigo QR de resultados : Genera un codigo QR de resultados para exhibir en el lugar de la competicion para los espectadores.",
                ],
                'tip_es': 'La imagen automatica del podio esta formateada para Instagram Stories (9:16) y Facebook (16:9).',
            },
            3: {
                'title_es': 'Exportar los resultados (CSV/PDF)',
                'steps_es': [
                    "Acceder a la exportacion : Desde Resultados > Exportar, elige el formato: CSV (datos brutos), PDF (informe formateado) o Excel.",
                    "Elegir el contenido : Selecciona: Clasificacion general, Solo podios, Detalle por categoria, Informe de medallas por club o Todo.",
                    "Personalizar el PDF : Para el PDF, elige la plantilla: informe oficial (con logo de la federacion), informe simple o diplomas.",
                ],
                'tip_es': 'El informe de medallas por club es particularmente util para federaciones y patrocinadores.',
            },
            4: {
                'title_es': 'Consultar tu palmares personal',
                'steps_es': [
                    "Acceder a Mi palmares : Desde tu perfil de practicante, haz clic en 'Palmares'. Tu historial de competiciones se muestra.",
                    "Ver las estadisticas : Consulta: numero de competiciones, medallas (oro/plata/bronce), porcentaje de victorias, progresion en el tiempo.",
                    "Compartir tu palmares : Genera un enlace publico a tu palmares o exportalo en PDF para tus expedientes de candidatura o patrocinio.",
                ],
                'tip_es': 'Tu palmares se actualiza automaticamente despues de cada competicion. Es visible en tu perfil publico si lo permites.',
            },
        },
    },

    # =========================================================================
    # Seccion 8: Gestion de Grados (5 tutoriales)
    # =========================================================================
    8: {
        'title_es': 'Gestion de Grados',
        'tutorials': {
            1: {
                'title_es': 'Configurar el sistema de grados',
                'steps_es': [
                    "Acceder a la configuracion : Desde Configuracion > Grados, selecciona la disciplina y define tu sistema de grados.",
                    "Crear los niveles : Agrega los niveles en orden: Cinturon blanco, Amarillo, Naranja, Verde, Azul, Marron, Negro 1er Dan, 2o Dan, etc.",
                    "Definir los prerequisitos : Para cada grado, define: tiempo minimo en el grado anterior, edad minima, numero minimo de clases, si se requiere examen.",
                    "Asignar los colores : Asigna los colores de los cinturones para la visualizacion en la interfaz y los perfiles.",
                ],
                'tip_es': 'Los sistemas de grados estandar (Judo, Karate, TKD, BJJ) estan preconfigurados. Puedes personalizarlos o crear nuevos.',
            },
            2: {
                'title_es': 'Asignar un grado a un practicante',
                'steps_es': [
                    "Acceder a la ficha : Desde la ficha del practicante, haz clic en la pestana Grados y luego en 'Asignar un nuevo grado'.",
                    "Seleccionar el grado : Elige el grado de la lista. El sistema verifica automaticamente los prerequisitos (tiempo, edad, examenes).",
                    "Ingresar los detalles : Agrega la fecha de asignacion, el lugar, el jurado/examinador y las observaciones.",
                    "Asignacion masiva : Desde Grados > Asignacion masiva, selecciona varios practicantes y asigna el mismo grado a todos.",
                ],
                'tip_es': 'Un email de felicitacion se envia automaticamente al practicante con su nuevo grado.',
            },
            3: {
                'title_es': 'Organizar un examen de grado',
                'steps_es': [
                    "Crear el examen : Desde Grados > Examenes, crea un nuevo examen: fecha, lugar, disciplina, grados cubiertos, jurado.",
                    "Inscribir candidatos : Agrega los candidatos manualmente o permite la auto-inscripcion. El sistema verifica los prerequisitos de cada uno.",
                    "El dia del examen : Usa la interfaz de examen para evaluar a cada candidato: tecnicas requeridas, combate, teoria.",
                    "Publicar los resultados : Valida los aprobados y reprobados. Los grados se asignan automaticamente a los candidatos que aprobaron.",
                ],
                'tip_es': 'Los examenes de grado pueden vincularse a una competicion (ej. promocion de grado durante un torneo).',
            },
            4: {
                'title_es': 'Gestionar el historial y la progresion de grados',
                'steps_es': [
                    "Ver el historial : La ficha de cada practicante muestra el historial completo de grados: fecha, lugar, jurado, observaciones.",
                    "Visualizar la progresion : Un grafico muestra la progresion en el tiempo. Compara con el promedio del club.",
                    "Revocar un grado : En caso de error, revoca un grado con un motivo. El historial conserva el registro de la revocacion.",
                ],
                'tip_es': 'El historial de grados es transferible si el practicante cambia de club.',
            },
            5: {
                'title_es': 'Generar certificados de grado',
                'steps_es': [
                    "Acceder a los certificados : Desde Grados > Certificados, selecciona el practicante y el grado para el que generar un certificado.",
                    "Elegir la plantilla : Selecciona una plantilla de certificado: oficial (con logo de federacion), club o personalizada.",
                    "Personalizar : Agrega las firmas, el sello del club y las menciones especiales. El codigo QR de verificacion se agrega automaticamente.",
                    "Generar y distribuir : Genera el PDF. Imprime o envia por email. El codigo QR permite a cualquiera verificar la autenticidad del certificado.",
                ],
                'tip_es': 'El codigo QR de verificacion dirige a una pagina publica de MartialComp que confirma la validez del grado.',
            },
        },
    },

    # =========================================================================
    # Seccion 9: Gestion de la Federacion (8 tutoriales)
    # =========================================================================
    9: {
        'title_es': 'Gestion de la Federacion',
        'tutorials': {
            1: {
                'title_es': 'Gestionar los clubes afiliados',
                'steps_es': [
                    "Vista general : El panel de la federacion muestra el mapa de clubes afiliados, su estado (activo, pendiente, vencido) y estadisticas.",
                    "Procesar las solicitudes : Las nuevas solicitudes de afiliacion aparecen en Clubes > Pendientes. Revisa los documentos y aprueba o rechaza.",
                    "Monitorear las renovaciones : Visualiza las afiliaciones proximas a vencer. Envia recordatorios automaticos 30, 15 y 7 dias antes.",
                ],
                'tip_es': 'El panel de la federacion proporciona una vision en tiempo real del numero total de practicantes licenciados en todos los clubes.',
            },
            2: {
                'title_es': 'Gestionar temporadas y cuotas',
                'steps_es': [
                    "Crear una temporada : Desde Temporadas > Nueva, define las fechas de inicio y fin y las tarifas de cuotas por tipo (club, individual, junior, senior).",
                    "Configurar las cuotas : Define los montos por categoria: afiliacion del club (fijo), licencia individual (por practicante), seguro (opcional).",
                    "Monitorear los pagos : Visualiza las cuotas recibidas, pendientes y vencidas en tiempo real. Envia recordatorios automaticos.",
                    "Cerrar la temporada : Al final de la temporada, cierrala para generar el informe financiero y preparar la siguiente temporada.",
                ],
                'tip_es': 'Las cuotas pueden pagarse online via Stripe o por transferencia bancaria. El seguimiento es automatico en ambos casos.',
            },
            3: {
                'title_es': 'Supervisar las competiciones',
                'steps_es': [
                    "Vision global : El calendario de la federacion muestra todas las competiciones de los clubes afiliados, con estado y numero de participantes.",
                    "Homologar una competicion : Los clubes envian sus competiciones para homologacion. Verifica las reglas, los jueces y valida.",
                    "Ver los resultados : Accede a los resultados de todas las competiciones homologadas. Las clasificaciones nacionales se actualizan automaticamente.",
                ],
                'tip_es': 'Las competiciones homologadas por la federacion se destacan en el directorio y el calendario publico.',
            },
            4: {
                'title_es': 'Gestionar los jueces y sus cualificaciones',
                'steps_es': [
                    "Base de datos de jueces : Visualiza la base de datos de jueces afiliados con sus cualificaciones, especialidades e historial de actividad.",
                    "Gestionar los niveles : Asigna niveles de cualificacion: regional, nacional, internacional. Define los criterios de promocion.",
                    "Seguimiento de neutralidad : MartialComp analiza las estadisticas de puntuacion de cada juez y detecta posibles sesgos.",
                ],
                'tip_es': 'Los jueces con un historial de puntuacion equilibrado se destacan para las competiciones importantes.',
            },
            5: {
                'title_es': 'Gestionar las certificaciones',
                'steps_es': [
                    "Crear una plantilla : Disena tus plantillas de certificado con el logo de la federacion, las menciones legales y los campos dinamicos.",
                    "Emitir certificados : Genera certificados para: grados, cualificaciones de jueces, diplomas de ensenanza, varias atestaciones.",
                    "Verificacion publica : Cada certificado tiene un codigo QR unico. Cualquiera puede escanearlo para verificar la autenticidad en martialcomp.com.",
                ],
                'tip_es': 'Los certificados digitales son a prueba de manipulacion gracias al codigo QR de verificacion vinculado a MartialComp.',
            },
            6: {
                'title_es': 'Personalizar el sitio publico de la federacion',
                'steps_es': [
                    "Acceder al constructor del sitio : Desde Configuracion > Sitio publico, abre el editor de pagina. Tu federacion tiene una URL: federacion.martialcomp.com.",
                    "Personalizar la apariencia : Elige colores, tema, banner y logo. Agrega una descripcion y los enlaces a tus redes sociales.",
                    "Agregar contenido : Publica noticias, galerias de fotos, videos, calendario de competiciones y documentos descargables.",
                    "Gestionar las paginas : Crea paginas adicionales: Historia, Directivos, Reglamento, Contacto.",
                ],
                'tip_es': 'El sitio publico esta optimizado para SEO. Cuanto mas completo este, mejor se posicionara en Google.',
            },
            7: {
                'title_es': 'Ver estadisticas e informes',
                'steps_es': [
                    "Panel analitico : El panel muestra los KPIs: numero de clubes, practicantes, competiciones, licencias activas, crecimiento.",
                    "Informes por club : Genera informes detallados por club: numero de miembros, cuotas, participacion en competiciones, grados otorgados.",
                    "Informes por disciplina : Analiza la distribucion por disciplina, edad, sexo. Identifica las tendencias de crecimiento.",
                    "Exportar y compartir : Exporta los informes en PDF, Excel o CSV para tus asambleas generales e informes oficiales.",
                ],
                'tip_es': 'Los informes se actualizan en tiempo real. Programa envios automaticos mensuales o trimestrales.',
            },
            8: {
                'title_es': 'Gestionar los programas de formacion',
                'steps_es': [
                    "Crear un programa : Desde Formacion > Nuevo, define el programa: titulo, disciplina, nivel, duracion, prerequisitos.",
                    "Planificar las sesiones : Agrega las sesiones de formacion: fechas, lugares, formadores, numero de plazas.",
                    "Gestionar las inscripciones : Entrenadores y jueces se inscriben online. Valida las inscripciones y envia las convocatorias.",
                    "Seguimiento y certificacion : Monitorea la asistencia a las sesiones. Emite las certificaciones a los participantes que completaron el programa.",
                ],
                'tip_es': 'Los programas de formacion completados aparecen automaticamente en los perfiles de entrenadores y jueces.',
            },
        },
    },

    # =========================================================================
    # Seccion 10: Finanzas (5 tutoriales)
    # =========================================================================
    10: {
        'title_es': 'Finanzas',
        'tutorials': {
            1: {
                'title_es': 'Monitorear las transacciones del club',
                'steps_es': [
                    "Vista general : El panel financiero muestra: saldo, ingresos del mes, gastos y grafico de tendencias.",
                    "Registrar una transaccion : Agrega un ingreso o gasto: monto, fecha, categoria (cuotas, equipamiento, alquiler), descripcion.",
                    "Categorizacion automatica : MartialComp categoriza automaticamente las transacciones recurrentes. Personaliza las categorias segun tus necesidades.",
                ],
                'tip_es': 'Conecta tu cuenta bancaria para importar automaticamente las transacciones y simplificar la conciliacion.',
            },
            2: {
                'title_es': 'Crear y enviar facturas',
                'steps_es': [
                    "Crear una factura : Desde Finanzas > Facturas > Nueva, selecciona el destinatario (practicante, club, patrocinador) y las lineas de facturacion.",
                    "Personalizar : Agrega tu logo, las notas legales, los terminos de pago. Elige la moneda y la tasa de IVA.",
                    "Enviar : Envia la factura por email. El destinatario recibe un enlace de pago online (Stripe) y la factura en PDF.",
                    "Monitorear los pagos : Visualiza las facturas pagadas, pendientes y vencidas. Envia recordatorios automaticos.",
                ],
                'tip_es': 'Las cuotas de los practicantes generan automaticamente facturas si activas esta opcion.',
            },
            3: {
                'title_es': 'Gestionar los pagos online (Stripe)',
                'steps_es': [
                    "Conectar Stripe : Desde Configuracion > Pagos, haz clic en 'Conectar Stripe'. Sigue los pasos para vincular tu cuenta de Stripe.",
                    "Configurar el checkout : Establece las tarifas para: cuotas, inscripciones a competiciones, tienda. Activa los pagos recurrentes si es necesario.",
                    "Probar el pago : Usa el modo de prueba de Stripe para verificar que todo funcione antes de activar los pagos reales.",
                    "Monitorear los ingresos : El panel de Stripe en MartialComp muestra los pagos recibidos, reembolsos y transferencias a tu cuenta bancaria.",
                ],
                'tip_es': 'Stripe cobra una comision del 1,4% + 0,25 EUR por transaccion en Europa. Los fondos se transfieren en 2-7 dias.',
            },
            4: {
                'title_es': 'Importar extractos bancarios',
                'steps_es': [
                    "Descargar el extracto : Desde tu banco, exporta el extracto en formato CSV, OFX o QIF.",
                    "Importar en MartialComp : Desde Finanzas > Importar, carga el archivo. MartialComp detecta el formato y mapea las columnas.",
                    "Conciliar : El sistema empareja automaticamente las transacciones importadas con las facturas y cuotas existentes.",
                    "Validar : Verifica los emparejamientos, corrige errores y valida. Las transacciones sin emparejar se agregan como pendientes.",
                ],
                'tip_es': 'Las importaciones bancarias mensuales mantienen tu contabilidad al dia sin ingreso manual.',
            },
            5: {
                'title_es': 'Gestionar las cuotas de los practicantes',
                'steps_es': [
                    "Configurar las tarifas : Desde Finanzas > Cuotas, establece las tarifas anuales por categoria: nino, adolescente, adulto, familia.",
                    "Emitir las solicitudes de pago : Al inicio de la temporada, genera las solicitudes de pago para todos los miembros. Cada uno recibe un email con un enlace de pago.",
                    "Monitorear los pagos : Visualiza las cuotas pagadas, pendientes y vencidas. El estado aparece en la ficha de cada practicante.",
                    "Enviar recordatorios : Programa recordatorios automaticos: 1 semana, 2 semanas, 1 mes despues de la fecha de vencimiento.",
                ],
                'tip_es': 'Los practicantes con cuotas vencidas pueden ser bloqueados de la inscripcion a competiciones.',
            },
        },
    },

    # =========================================================================
    # Seccion 11: Eventos y Calendario (3 tutoriales)
    # =========================================================================
    11: {
        'title_es': 'Eventos y Calendario',
        'tutorials': {
            1: {
                'title_es': 'Crear un evento (seminario, gala, asamblea)',
                'steps_es': [
                    "Crear el evento : Desde Calendario > Nuevo evento, ingresa: tipo (seminario, gala, asamblea, puertas abiertas), titulo, fechas, lugar y descripcion.",
                    "Configurar las inscripciones : Activa las inscripciones online. Establece el numero de plazas, la tarifa (gratuita o de pago) y la fecha limite de inscripcion.",
                    "Publicar : Publica el evento. Aparece en el calendario del club y puede compartirse en redes sociales.",
                ],
                'tip_es': 'Los seminarios con maestros invitados son excelentes herramientas de marketing. Agrega su foto y biografia para atraer mas personas.',
            },
            2: {
                'title_es': 'Gestionar los eventos recurrentes',
                'steps_es': [
                    "Crear la recurrencia : Durante la creacion, marca 'Evento recurrente'. Establece la frecuencia: diaria, semanal, mensual.",
                    "Gestionar excepciones : Cancela o modifica una ocurrencia individual sin afectar las demas (ej. clase cancelada por festivo).",
                    "Modificar la serie : Modifica toda la serie (ej. cambio permanente de horario) o una sola ocurrencia.",
                ],
                'tip_es': 'Las clases semanales deben crearse como eventos recurrentes para aparecer automaticamente en el calendario.',
            },
            3: {
                'title_es': 'Monitorear inscripciones y asistencia',
                'steps_es': [
                    "Ver los inscritos : Desde el evento, visualiza la lista de inscritos con su estado: inscrito, confirmado, cancelado.",
                    "Registrar la asistencia : El dia del evento, registra la asistencia por lista o codigo QR.",
                    "Exportar : Exporta la lista de participantes en CSV o PDF para tus archivos.",
                ],
                'tip_es': 'La tasa de participacion en eventos es un indicador clave del compromiso de tus miembros.',
            },
        },
    },

    # =========================================================================
    # Seccion 12: Gestion Familiar (3 tutoriales)
    # =========================================================================
    12: {
        'title_es': 'Gestion Familiar',
        'tutorials': {
            1: {
                'title_es': 'Crear un grupo familiar',
                'steps_es': [
                    "Acceder a los grupos familiares : Desde tu perfil, ve a Configuracion > Grupo Familiar > Crear.",
                    "Agregar miembros : Agrega a cada miembro de la familia: conyuge, hijos. Vincula sus cuentas MartialComp existentes o crea nuevas.",
                    "Establecer el responsable : El responsable del grupo familiar recibe todas las notificaciones y gestiona los pagos de toda la familia.",
                ],
                'tip_es': 'Algunos clubes ofrecen tarifas familiares (descuento a partir del 3er miembro). El grupo familiar activa automaticamente estos descuentos.',
            },
            2: {
                'title_es': 'Inscribir a toda la familia en una competicion',
                'steps_es': [
                    "Inscripcion grupal : Desde la competicion, haz clic en 'Inscribir a mi familia'. Se muestran los miembros elegibles de tu grupo familiar.",
                    "Seleccionar y confirmar : Selecciona los miembros a inscribir. Las categorias se sugieren automaticamente para cada uno.",
                    "Pago unico : Paga todas las inscripciones en una sola transaccion.",
                ],
                'tip_es': 'La inscripcion grupal ahorra tiempo valioso cuando varios hijos participan en la misma competicion.',
            },
            3: {
                'title_es': 'Centro de pagos familiar',
                'steps_es': [
                    "Vista general : El centro familiar muestra todas las cuotas, inscripciones y facturas de la familia en una sola pantalla.",
                    "Pago agrupado : Agrupa varios pagos pendientes y paga en una sola transaccion.",
                    "Historial : Visualiza el historial completo de pagos de la familia con recibos descargables.",
                ],
                'tip_es': 'Activa el debito directo automatico para no olvidar nunca una cuota.',
            },
        },
    },

    # =========================================================================
    # Seccion 13: Gestion de Tareas (Kanban) (2 tutoriales)
    # =========================================================================
    13: {
        'title_es': 'Gestion de Tareas (Kanban)',
        'tutorials': {
            1: {
                'title_es': 'Usar el tablero Kanban',
                'steps_es': [
                    "Crear un tablero : Desde Herramientas > Kanban, crea un nuevo tablero: nombre, descripcion y miembros invitados.",
                    "Agregar columnas : Crea las columnas de tu flujo de trabajo: Por hacer, En curso, En espera, Hecho. Personaliza nombres y colores.",
                    "Crear tareas : Agrega tareas con: titulo, descripcion, fecha limite, responsable, prioridad (alta/media/baja) y etiquetas.",
                    "Gestionar arrastrando y soltando : Mueve las tareas entre columnas arrastandolas. El historial de movimientos se conserva.",
                ],
                'tip_es': 'Crea un tablero dedicado para cada competicion a organizar. Las tareas estandar (reservar el lugar, pedir medallas, etc.) pueden importarse desde una plantilla.',
            },
            2: {
                'title_es': 'Gestionar las tareas organizativas',
                'steps_es': [
                    "Plantilla de competicion : Usa la plantilla 'Organizacion de Competicion' que contiene tareas estandar: logistica, comunicacion, jueces, medallas, etc.",
                    "Asignar a los miembros : Asigna cada tarea a un miembro del equipo organizador. Establece los plazos.",
                    "Monitorear el progreso : El porcentaje de avance general se muestra en la parte superior del tablero. Las tareas vencidas se resaltan en rojo.",
                ],
                'tip_es': 'El tablero Kanban es accesible desde la app movil para actualizar las tareas sobre la marcha.',
            },
        },
    },

    # =========================================================================
    # Seccion 14: Tienda Online (2 tutoriales)
    # =========================================================================
    14: {
        'title_es': 'Tienda Online',
        'tutorials': {
            1: {
                'title_es': 'Configurar la tienda del club',
                'steps_es': [
                    "Activar la tienda : Desde Configuracion > Tienda, activa la funcionalidad de comercio electronico. Conecta tu cuenta Stripe si aun no lo has hecho.",
                    "Agregar productos : Crea tus productos: nombre, descripcion, fotos, precio, tallas/variantes disponibles, stock.",
                    "Organizar por categorias : Clasifica tus productos: Uniformes (kimono, dobok, guantes), Equipamiento (protecciones, bolsas), Accesorios (cinturones, parches), Merchandising.",
                    "Publicar la tienda : Tu tienda es accesible desde la pagina publica de tu club. Comparte el enlace o codigo QR.",
                ],
                'tip_es': 'Ofrece paquetes (kimono + cinturon + bolsa) con descuento para aumentar el ticket promedio.',
            },
            2: {
                'title_es': 'Realizar un pedido',
                'steps_es': [
                    "Navegar por la tienda : Desde la pagina de tu club, accede a la tienda. Navega por los productos por categoria.",
                    "Agregar al carrito : Selecciona la talla/variante y agrega al carrito. El carrito se mantiene entre sesiones.",
                    "Pedir y pagar : Confirma tu carrito, elige el metodo de entrega (recogida en el dojo o envio postal) y paga online.",
                    "Monitorear el pedido : Recibe notificaciones en cada paso: pedido confirmado, en preparacion, listo para recoger / enviado.",
                ],
                'tip_es': 'El modo \'Recogida en el Dojo\' evita gastos de envio. El entrenador te entregara tu pedido en la proxima clase.',
            },
        },
    },

    # =========================================================================
    # Seccion 15: Funcionalidades Avanzadas (5 tutoriales)
    # =========================================================================
    15: {
        'title_es': 'Funcionalidades Avanzadas',
        'tutorials': {
            1: {
                'title_es': 'Configurar el streaming de competiciones',
                'steps_es': [
                    "Preparar el streaming : Crea un evento en vivo en YouTube, Twitch o Facebook. Copia la URL del streaming y la clave de streaming.",
                    "Configurar en MartialComp : Desde la competicion, ve a Configuracion > Streaming. Pega la URL y activa la visualizacion en la pagina publica.",
                    "Overlay de puntuacion : Activa el overlay de MartialComp que muestra la puntuacion en vivo en el streaming de video. Personaliza la posicion y el estilo.",
                    "Iniciar y probar : Inicia el streaming y verifica que el overlay funcione. Los espectadores veran la puntuacion en vivo en el streaming.",
                ],
                'tip_es': 'El streaming con overlay de puntuacion de MartialComp da un aspecto profesional incluso a las competiciones pequenas.',
            },
            2: {
                'title_es': 'Usar la aplicacion movil',
                'steps_es': [
                    "Descargar la app : Busca 'MartialComp' en el Play Store (Android) o App Store (iOS). Instala y abre.",
                    "Iniciar sesion : Inicia sesion con tu cuenta MartialComp existente. Tambien puedes usar el acceso con Google, Facebook o Apple.",
                    "Descubrir la interfaz movil : La app ofrece: perfil, resultados, calendario, notificaciones push, codigo QR personal e inscripcion a competiciones.",
                    "Modo sin conexion : Los datos esenciales (perfil, grado, licencia) estan disponibles sin conexion. Sincronizacion automatica al volver a conectarse.",
                ],
                'tip_es': 'Activa las notificaciones push para recibir alertas de resultados en vivo durante las competiciones.',
            },
            3: {
                'title_es': 'Cambiar de rol en la aplicacion',
                'steps_es': [
                    "Acceder al selector de rol : Toca tu avatar en la parte superior de la pantalla o desliza desde la izquierda para abrir el menu lateral.",
                    "Seleccionar un rol : Aparece tu lista de roles: Entrenador, Practicante, Juez, Responsable de Club. Toca el rol deseado.",
                    "Interfaz adaptada : El panel de control y el menu se actualizan inmediatamente para reflejar el rol seleccionado.",
                ],
                'tip_es': 'Puedes ser entrenador en un club y practicante en otro. Cada rol esta vinculado a su organizacion.',
            },
            4: {
                'title_es': 'Importacion/Exportacion avanzada de datos',
                'steps_es': [
                    "Formatos soportados : MartialComp soporta la importacion y exportacion en CSV, Excel (XLSX), JSON y PDF. Cada modulo tiene sus propias opciones.",
                    "Importacion con mapeo : La interfaz de mapeo permite asociar cualquier estructura de archivo con los campos de MartialComp.",
                    "Exportacion personalizada : Selecciona los campos a exportar, los filtros y el formato. Programa exportaciones automaticas recurrentes.",
                    "Operaciones masivas : Las operaciones masivas permiten la modificacion en masa de: grado, grupo, estado de inscripcion, etc.",
                ],
                'tip_es': 'La exportacion JSON es ideal para integraciones con sistemas de terceros (sitio web, aplicacion externa, CRM).',
            },
            5: {
                'title_es': 'Gestionar jueces ad hoc (voluntarios)',
                'steps_es': [
                    "Crear un juez temporal : El dia de la competicion, desde Jueces > Agregar voluntario, crea un perfil temporal: nombre, club y especialidad.",
                    "Asignar un PIN : Un PIN unico se genera automaticamente. El voluntario usa este PIN para acceder a la interfaz de puntuacion.",
                    "Asignar a las categorias : Asigna al juez voluntario a las categorias como a un juez regular. Puede comenzar a evaluar inmediatamente.",
                    "Despues de la competicion : El perfil temporal se archiva despues de la competicion. Las puntuaciones se conservan en el historial.",
                ],
                'tip_es': 'Los jueces ad hoc son esenciales para competiciones pequenas donde el numero de jueces oficiales es limitado.',
            },
        },
    },
}


class Command(BaseCommand):
    help = 'Translate all 81 tutorials from French to Spanish (hardcoded translations)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Show what would be updated without saving to database'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - no changes will be saved'))

        sections_updated = 0
        tutorials_updated = 0
        sections_missing = 0
        tutorials_missing = 0

        for section in TutorialSection.objects.all().order_by('order'):
            sec_data = TRANSLATIONS.get(section.order)
            if not sec_data:
                self.stdout.write(self.style.WARNING(
                    f'  No translation for section {section.order}: {section.title}'
                ))
                sections_missing += 1
                continue

            section.title_es = sec_data['title_es']
            if not dry_run:
                section.save(update_fields=['title_es'])
            sections_updated += 1
            self.stdout.write(self.style.SUCCESS(
                f'  Section {section.order}: {section.title_fr} -> {sec_data["title_es"]}'
            ))

            for tutorial in section.tutorials.all().order_by('number'):
                tut_data = sec_data.get('tutorials', {}).get(tutorial.number)
                if not tut_data:
                    self.stdout.write(self.style.WARNING(
                        f'    No translation for tutorial {section.order}.{tutorial.number}: {tutorial.title}'
                    ))
                    tutorials_missing += 1
                    continue

                tutorial.title_es = tut_data['title_es']
                tutorial.steps_es = json.dumps(tut_data['steps_es'], ensure_ascii=False)
                tutorial.tip_es = tut_data.get('tip_es', '')

                if not dry_run:
                    tutorial.save(update_fields=['title_es', 'steps_es', 'tip_es'])

                tutorials_updated += 1
                self.stdout.write(f'    {section.order}.{tutorial.number}: {tut_data["title_es"]}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Translation complete: {sections_updated} sections, {tutorials_updated} tutorials updated'
        ))
        if sections_missing or tutorials_missing:
            self.stdout.write(self.style.WARNING(
                f'Missing translations: {sections_missing} sections, {tutorials_missing} tutorials'
            ))
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - no changes were saved'))
