# Análisis de Neutralidad de los Jueces

## Objetivo

El módulo de análisis de neutralidad permite evaluar objetivamente la imparcialidad de cada juez durante una competición. Detecta automáticamente los sesgos potenciales comparando las notas asignadas según varios criterios estadísticos.

Este módulo es una herramienta de **formación y mejora continua** para los jueces, y no una herramienta disciplinaria. Permite a cada juez tomar conciencia de sus tendencias inconscientes para progresar.

---

## Puntuación de Neutralidad (0-100)

Cada juez recibe una **puntuación global de neutralidad** calculada sobre 100 puntos. Cuanto más alta es la puntuación, más imparcial se considera al juez.

La puntuación se calcula restando penalizaciones a la puntuación perfecta de 100, según 4 criterios ponderados:

| Criterio | Peso | Penalización máxima |
|----------|------|---------------------|
| Sesgo de club | 30% | -30 puntos |
| Sesgo de nacionalidad | 25% | -25 puntos |
| Sesgo de posicionamiento | 20% | -20 puntos |
| Concordancia con los pares | 25% | -25 puntos |

### Niveles de riesgo

| Puntuación | Nivel | Significado |
|------------|-------|-------------|
| **80-100** | Riesgo bajo (verde) | El juez puntúa de manera coherente e imparcial |
| **60-79** | Riesgo moderado (naranja) | Tendencias detectadas, a vigilar |
| **0-59** | Riesgo alto (rojo) | Sesgos significativos detectados, formación recomendada |

---

## Criterio 1: Sesgo de Club

### Principio
Este criterio compara la media de las notas que un juez asigna a los practicantes de **su propio club** con respecto a los practicantes **de otros clubes**.

### Cálculo
```
Diferencia = Media(notas a practicantes del mismo club) - Media(notas a los otros practicantes)
```

### Umbrales de detección

| Diferencia (valor absoluto) | Severidad | Interpretación |
|-----------------------------|-----------|----------------|
| < 0,3 puntos | Neutro | No se detecta sesgo |
| 0,3 a 0,5 puntos | Bajo | Leve favoritismo o desfavorecimiento |
| 0,5 a 0,8 puntos | Moderado | Tendencia significativa a vigilar |
| > 0,8 puntos | Alto | Sesgo marcado, acción correctiva recomendada |

### Cómo interpretar
- **Valor positivo** (+): el juez tiende a puntuar más favorablemente a los practicantes de su club
- **Valor negativo** (-): el juez tiende a ser más severo con los practicantes de su club (sobrecompensación)
- Ambas situaciones son sesgos a corregir

### Penalización en la puntuación global

| Severidad | Penalización |
|-----------|-------------|
| Neutro | 0 puntos |
| Bajo | -10 puntos |
| Moderado | -20 puntos |
| Alto | -30 puntos |

---

## Criterio 2: Sesgo de Nacionalidad

### Principio
Este criterio compara la media de las notas asignadas a los practicantes de **la misma nacionalidad** que el juez con respecto a los practicantes **de otras nacionalidades**.

### Cálculo
```
Diferencia = Media(notas misma nacionalidad) - Media(notas otras nacionalidades)
```

### Umbrales de detección

| Diferencia (valor absoluto) | Severidad | Interpretación |
|-----------------------------|-----------|----------------|
| < 0,2 puntos | Neutro | No se detecta sesgo |
| 0,2 a 0,4 puntos | Bajo | Leve favoritismo o desfavorecimiento |
| 0,4 a 0,6 puntos | Moderado | Tendencia significativa |
| > 0,6 puntos | Alto | Sesgo marcado |

### Cómo interpretar
- **Umbrales más estrictos** que el sesgo de club, porque la nacionalidad no debería tener ninguna influencia en la puntuación técnica
- **Valor positivo**: favoritismo hacia su nacionalidad
- **Valor negativo**: severidad excesiva hacia su nacionalidad

### Penalización en la puntuación global

| Severidad | Penalización |
|-----------|-------------|
| Neutro | 0 puntos |
| Bajo | -8 puntos |
| Moderado | -16 puntos |
| Alto | -25 puntos |

---

## Criterio 3: Sesgo de Posicionamiento

### Principio
Este criterio compara la **media general de las notas** de un juez con respecto a la **media de todos los jueces** de la competición. Detecta a los jueces sistemáticamente demasiado generosos o demasiado severos.

### Cálculo
```
Diferencia = Media(todas las notas del juez) - Media(todas las notas de todos los jueces)
```

### Umbrales de detección

| Diferencia (valor absoluto) | Severidad | Interpretación |
|-----------------------------|-----------|----------------|
| < 0,2 puntos | Neutro | En la media, puntuación calibrada |
| 0,2 a 0,4 puntos | Bajo | Ligeramente generoso o severo |
| 0,4 a 0,6 puntos | Moderado | Generoso o severo de manera notable |
| > 0,6 puntos | Alto | Muy generoso o muy severo |

### Cómo interpretar
- **Valor positivo** (+): el juez puntúa sistemáticamente por encima de la media (generoso)
- **Valor negativo** (-): el juez puntúa sistemáticamente por debajo de la media (severo)
- Un buen juez se sitúa en el rango neutro (< 0,2 puntos de desviación)

### Penalización en la puntuación global

| Severidad | Penalización |
|-----------|-------------|
| Neutro | 0 puntos |
| Bajo | -5 puntos |
| Moderado | -12 puntos |
| Alto | -20 puntos |

---

## Criterio 4: Concordancia con los Pares

### Principio
Este criterio mide en qué medida las notas de un juez están **en concordancia con las de los otros jueces** para las mismas actuaciones. Un juez cuyas notas divergen constantemente de las de sus colegas puede presentar un problema de calibración o de sesgo.

### Cálculo
Para cada actuación puntuada por el juez:
```
Media de los otros = Media(notas de los otros jueces para esta actuación)
Desviación = |Nota del juez - Media de los otros|
Concordancia individual = max(0, 100 - (Desviación × 20))
```

La **puntuación de concordancia global** es la media de todas las concordancias individuales.

### Interpretación

| Concordancia | Significado |
|--------------|-------------|
| **90-100%** | Excelente concordancia, puntuación muy alineada |
| **75-89%** | Buena concordancia |
| **60-74%** | Concordancia aceptable pero a mejorar |
| **< 60%** | Concordancia baja, **alerta generada** |

### Impacto en la puntuación global
La concordancia influye en la puntuación de neutralidad mediante un bonus/malus:
```
Ajuste = (Concordancia - 50) / 2
```
- Concordancia del 100%: bonus de +25 puntos
- Concordancia del 50%: ni bonus ni malus
- Concordancia del 0%: malus de -25 puntos

### Condiciones
- Se requiere un mínimo de **3 actuaciones** puntuadas para que el cálculo sea significativo
- Solo se tienen en cuenta las notas activas (no las de entrenamiento)

---

## Sistema de Alertas

Se generan alertas automáticamente en los siguientes casos:

| Condición | Alerta |
|-----------|--------|
| Sesgo de club moderado o alto | "Sesgo de club detectado" con el valor de desviación |
| Sesgo de nacionalidad moderado o alto | "Sesgo de nacionalidad detectado" con el valor de desviación |
| Posicionamiento alto únicamente | "Posición extrema" con la desviación respecto a la media |
| Concordancia < 60% | "Baja concordancia con los otros jueces" |

Las alertas son visibles en la ficha detallada de cada juez en la interfaz de análisis.

---

## Podio de los Jueces Más Imparciales

Al final del análisis, un **podio** destaca a los 3 jueces que obtuvieron las mejores puntuaciones de neutralidad:

- **1.er lugar (Oro)**: Puntuación de neutralidad más alta
- **2.º lugar (Plata)**: Segunda mejor puntuación
- **3.er lugar (Bronce)**: Tercera mejor puntuación

Este ranking recompensa la imparcialidad y anima al conjunto de los jueces a progresar.

---

## Recomendaciones para los Jueces

### Para mejorar su puntuación de neutralidad

1. **Sesgo de club**: Preste especial atención cuando puntúe a un practicante de su propio club. Aplique los mismos criterios técnicos que para los demás.

2. **Sesgo de nacionalidad**: Concéntrese únicamente en la técnica y la ejecución. La nacionalidad del practicante no debe influir en su evaluación.

3. **Posicionamiento**: Calibre sus notas alineándose con los criterios definidos. Ni demasiado generoso, ni demasiado severo. En caso de duda, consulte el baremo oficial.

4. **Concordancia**: Si sus notas divergen a menudo de las de sus colegas, esto puede indicar un problema de comprensión de los criterios. Participe en las sesiones de calibración.

### Buenas prácticas

- Puntúe cada actuación de manera independiente, sin mirar las notas de los otros jueces
- Utilice toda la extensión de la escala de puntuación
- No modifique sus notas después de haber visto las de los demás
- Tómese el tiempo de evaluar cada criterio por separado
- En caso de fatiga, haga una pausa para mantener su concentración

---

## Acceso y Confidencialidad

- El análisis de neutralidad es accesible para los **organizadores de competición** y los **administradores de federación**
- Cada juez puede consultar **sus propios resultados**
- Los datos se calculan en **tiempo real** a partir de las notas existentes (ningún dato de neutralidad se almacena de manera permanente)
- El análisis requiere un número suficiente de notas para ser fiable (mínimo 3 actuaciones para la concordancia)
