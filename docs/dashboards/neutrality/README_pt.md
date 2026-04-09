# Análise de Neutralidade dos Juízes

## Objetivo

O módulo de análise de neutralidade permite avaliar objetivamente a imparcialidade de cada juiz durante uma competição. Deteta automaticamente os vieses potenciais comparando as notas atribuídas segundo vários critérios estatísticos.

Este módulo é uma ferramenta de **formação e melhoria contínua** para os juízes, e não uma ferramenta disciplinar. Permite a cada juiz tomar consciência das suas tendências inconscientes a fim de progredir.

---

## Pontuação de Neutralidade (0-100)

Cada juiz recebe uma **pontuação global de neutralidade** calculada sobre 100 pontos. Quanto mais elevada a pontuação, mais o juiz é considerado imparcial.

A pontuação é calculada subtraindo penalizações à pontuação perfeita de 100, segundo 4 critérios ponderados:

| Critério | Peso | Penalização máxima |
|----------|------|-------------------|
| Viés de clube | 30% | -30 pontos |
| Viés de nacionalidade | 25% | -25 pontos |
| Viés de posicionamento | 20% | -20 pontos |
| Concordância com os pares | 25% | -25 pontos |

### Níveis de risco

| Pontuação | Nível | Significado |
|-----------|-------|-------------|
| **80-100** | Risco baixo (verde) | O juiz avalia de forma coerente e imparcial |
| **60-79** | Risco moderado (laranja) | Tendências detetadas, a vigiar |
| **0-59** | Risco elevado (vermelho) | Vieses significativos detetados, formação recomendada |

---

## Critério 1: Viés de Clube

### Princípio
Este critério compara a média das notas que um juiz atribui aos praticantes do **seu próprio clube** em relação aos praticantes **dos outros clubes**.

### Cálculo
```
Diferença = Média(notas aos praticantes do mesmo clube) - Média(notas aos outros praticantes)
```

### Limiares de deteção

| Diferença (valor absoluto) | Severidade | Interpretação |
|---------------------------|------------|---------------|
| < 0,3 ponto | Neutro | Sem viés detetado |
| 0,3 a 0,5 ponto | Fraco | Ligeiro favoritismo ou desfavoritismo |
| 0,5 a 0,8 ponto | Moderado | Tendência significativa a vigiar |
| > 0,8 ponto | Elevado | Viés acentuado, ação corretiva recomendada |

### Como interpretar
- **Valor positivo** (+): o juiz tende a avaliar mais favoravelmente os praticantes do seu clube
- **Valor negativo** (-): o juiz tende a ser mais severo com os praticantes do seu clube (sobrecompensação)
- Ambas as situações são vieses a corrigir

### Penalização na pontuação global

| Severidade | Penalização |
|------------|-------------|
| Neutro | 0 pontos |
| Fraco | -10 pontos |
| Moderado | -20 pontos |
| Elevado | -30 pontos |

---

## Critério 2: Viés de Nacionalidade

### Princípio
Este critério compara a média das notas atribuídas aos praticantes da **mesma nacionalidade** que o juiz em relação aos praticantes de **outras nacionalidades**.

### Cálculo
```
Diferença = Média(notas mesma nacionalidade) - Média(notas outras nacionalidades)
```

### Limiares de deteção

| Diferença (valor absoluto) | Severidade | Interpretação |
|---------------------------|------------|---------------|
| < 0,2 ponto | Neutro | Sem viés detetado |
| 0,2 a 0,4 ponto | Fraco | Ligeiro favoritismo ou desfavoritismo |
| 0,4 a 0,6 ponto | Moderado | Tendência significativa |
| > 0,6 ponto | Elevado | Viés acentuado |

### Como interpretar
- **Limiares mais rigorosos** do que o viés de clube, porque a nacionalidade não deveria ter qualquer influência na avaliação técnica
- **Valor positivo**: favoritismo em relação à sua nacionalidade
- **Valor negativo**: severidade excessiva em relação à sua nacionalidade

### Penalização na pontuação global

| Severidade | Penalização |
|------------|-------------|
| Neutro | 0 pontos |
| Fraco | -8 pontos |
| Moderado | -16 pontos |
| Elevado | -25 pontos |

---

## Critério 3: Viés de Posicionamento

### Princípio
Este critério compara a **média geral das notas** de um juiz em relação à **média de todos os juízes** da competição. Deteta os juízes sistematicamente demasiado generosos ou demasiado severos.

### Cálculo
```
Diferença = Média(todas as notas do juiz) - Média(todas as notas de todos os juízes)
```

### Limiares de deteção

| Diferença (valor absoluto) | Severidade | Interpretação |
|---------------------------|------------|---------------|
| < 0,2 ponto | Neutro | Dentro da média, avaliação calibrada |
| 0,2 a 0,4 ponto | Fraco | Ligeiramente generoso ou severo |
| 0,4 a 0,6 ponto | Moderado | Generoso ou severo de forma notável |
| > 0,6 ponto | Elevado | Muito generoso ou muito severo |

### Como interpretar
- **Valor positivo** (+): o juiz avalia sistematicamente acima da média (generoso)
- **Valor negativo** (-): o juiz avalia sistematicamente abaixo da média (severo)
- Um bom juiz situa-se na faixa neutra (< 0,2 ponto de desvio)

### Penalização na pontuação global

| Severidade | Penalização |
|------------|-------------|
| Neutro | 0 pontos |
| Fraco | -5 pontos |
| Moderado | -12 pontos |
| Elevado | -20 pontos |

---

## Critério 4: Concordância com os Pares

### Princípio
Este critério mede até que ponto as notas de um juiz estão **em acordo com as dos outros juízes** para as mesmas prestações. Um juiz cujas notas divergem constantemente dos seus colegas pode apresentar um problema de calibragem ou de viés.

### Cálculo
Para cada prestação avaliada pelo juiz:
```
Média dos outros = Média(notas dos outros juízes para esta prestação)
Desvio = |Nota do juiz - Média dos outros|
Concordância individual = max(0, 100 - (Desvio × 20))
```

A **pontuação de concordância global** é a média de todas as concordâncias individuais.

### Interpretação

| Concordância | Significado |
|-------------|-------------|
| **90-100%** | Excelente concordância, avaliação muito alinhada |
| **75-89%** | Boa concordância |
| **60-74%** | Concordância aceitável mas a melhorar |
| **< 60%** | Concordância fraca, **alerta gerado** |

### Impacto na pontuação global
A concordância influencia a pontuação de neutralidade através de um bónus/malus:
```
Ajuste = (Concordância - 50) / 2
```
- Concordância de 100%: bónus de +25 pontos
- Concordância de 50%: nem bónus nem malus
- Concordância de 0%: malus de -25 pontos

### Condições
- Um mínimo de **3 prestações** avaliadas é necessário para que o cálculo seja significativo
- Apenas as notas ativas (não de treino) são tidas em conta

---

## Sistema de Alertas

Alertas são automaticamente gerados nos seguintes casos:

| Condição | Alerta |
|----------|--------|
| Viés de clube moderado ou elevado | "Viés de clube detetado" com o valor do desvio |
| Viés de nacionalidade moderado ou elevado | "Viés de nacionalidade detetado" com o valor do desvio |
| Posicionamento elevado apenas | "Posição extrema" com o desvio em relação à média |
| Concordância < 60% | "Fraca concordância com os outros juízes" |

Os alertas são visíveis na ficha detalhada de cada juiz na interface de análise.

---

## Pódio dos Juízes Mais Imparciais

No final da análise, um **pódio** destaca os 3 juízes que obtiveram as melhores pontuações de neutralidade:

- **1.º lugar (Ouro)**: Pontuação de neutralidade mais elevada
- **2.º lugar (Prata)**: Segunda melhor pontuação
- **3.º lugar (Bronze)**: Terceira melhor pontuação

Esta classificação recompensa a imparcialidade e encoraja o conjunto dos juízes a progredir.

---

## Recomendações para os Juízes

### Para melhorar a sua pontuação de neutralidade

1. **Viés de clube**: Seja particularmente atento quando avalia um praticante do seu próprio clube. Aplique os mesmos critérios técnicos que para os outros.

2. **Viés de nacionalidade**: Concentre-se unicamente na técnica e na execução. A nacionalidade do praticante não deve influenciar a sua avaliação.

3. **Posicionamento**: Calibre as suas notas alinhando-se com os critérios definidos. Nem demasiado generoso, nem demasiado severo. Em caso de dúvida, consulte o barema oficial.

4. **Concordância**: Se as suas notas divergem frequentemente das dos seus colegas, isso pode indicar um problema de compreensão dos critérios. Participe nas sessões de calibragem.

### Boas práticas

- Avalie cada prestação de forma independente, sem olhar para as notas dos outros juízes
- Utilize toda a amplitude da escala de avaliação
- Não modifique as suas notas depois de ter visto as dos outros
- Reserve tempo para avaliar cada critério separadamente
- Em caso de fadiga, faça uma pausa para manter a sua concentração

---

## Acesso e Confidencialidade

- A análise de neutralidade é acessível aos **organizadores de competição** e aos **administradores de federação**
- Cada juiz pode consultar **os seus próprios resultados**
- Os dados são calculados em **tempo real** a partir das notas existentes (nenhum dado de neutralidade é armazenado de forma permanente)
- A análise necessita de um número suficiente de notas para ser fiável (mínimo de 3 prestações para a concordância)
