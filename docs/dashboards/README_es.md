# Paneles de Control MartialComp

## Introducción

Este directorio contiene la documentación completa de los diferentes paneles de control (dashboards) disponibles en la aplicación MartialComp. Cada tipo de usuario dispone de un panel de control específico para su rol, que ofrece funcionalidades adaptadas a sus necesidades.

## Tipos de Paneles de Control

MartialComp propone varios paneles de control, cada uno diseñado para un rol específico:

1. [**Panel de Participante**](./participants/README.md) - Para los practicantes de artes marciales que participan en competiciones
2. [**Panel de Club**](./clubs/README.md) - Para los gestores de clubes y sus administradores
3. [**Panel de Federación**](./federations/README.md) - Para los administradores de federaciones
4. [**Panel de Árbitro/Juez**](./referees/README.md) - Para los árbitros y jueces que evalúan las competiciones
5. [**Panel de Entrenador Multidisciplina**](./coaches/README.md) - Para los entrenadores que gestionan varias disciplinas
6. [**Panel de Combate**](./combat/README.md) - Interfaz especializada para la gestión de combates

## Acceso a los Paneles de Control

Cada usuario es redirigido automáticamente al panel de control correspondiente a su rol después de iniciar sesión. La redirección es gestionada por la vista `dashboard` en el archivo `competitions/views/dashboard/base.py`.

## Estructura Común de los Paneles de Control

Todos los paneles de control comparten una estructura común:

- **Encabezado**: Muestra el nombre del usuario, el rol, y da acceso a la configuración y al cierre de sesión
- **Barra lateral**: Navegación hacia las diferentes secciones del panel de control
- **Contenido principal**: Muestra la información y funcionalidades específicas de cada sección
- **Pie de página**: Información sobre la versión de la aplicación y enlaces útiles

## Personalización de los Paneles de Control

Los usuarios pueden personalizar ciertos aspectos de su panel de control:
- Elección de los widgets mostrados en la página principal
- Orden de visualización de la información
- Preferencias de notificación

## Funcionalidades Comunes

Todos los paneles de control ofrecen estas funcionalidades básicas:
- Vista general con estadísticas clave
- Notificaciones y alertas
- Gestión del perfil de usuario
- Calendario de eventos próximos
- Acceso a la documentación

## Soporte Multilingüe

Todos los paneles de control soportan el multilingüismo y están disponibles en los siguientes idiomas:
- Francés (fr) - Idioma predeterminado
- Inglés (en)
- Español (es)
- Italiano (it)
- Alemán (de)
- Noruego (no)
- Japonés (ja)
- Chino (zh)
- Hindi (hi)
- Árabe (ar)
- Suajili (sw)
- Amárico (am)
- Zulú (zu)
- Yoruba (yo)
- Portugués (pt)
- Coreano (ko)

## Diseño Técnico

Los paneles de control están implementados utilizando:
- Django para el backend
- HTML/CSS/JavaScript para el frontend
- Bootstrap para el diseño responsive
- Tecnología AJAX para las actualizaciones dinámicas

## Documentación Detallada

Para más detalles sobre cada panel de control, consulte los enlaces anteriores o explore las subcarpetas de este directorio.
