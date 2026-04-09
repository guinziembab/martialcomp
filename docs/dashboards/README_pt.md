# Painéis de Controlo MartialComp

## Introdução

Este diretório contém a documentação completa dos diferentes painéis de controlo (dashboards) disponíveis na aplicação MartialComp. Cada tipo de utilizador dispõe de um painel de controlo específico para o seu papel, oferecendo funcionalidades adaptadas às suas necessidades.

## Tipos de Painéis de Controlo

O MartialComp propõe vários painéis de controlo, cada um concebido para um papel específico:

1. [**Painel do Participante**](./participants/README.md) - Para os praticantes de artes marciais que participam em competições
2. [**Painel do Clube**](./clubs/README.md) - Para os gestores de clubes e seus administradores
3. [**Painel da Federação**](./federations/README.md) - Para os administradores de federações
4. [**Painel do Árbitro/Juiz**](./referees/README.md) - Para os árbitros e juízes que avaliam as competições
5. [**Painel do Treinador Multidisciplina**](./coaches/README.md) - Para os treinadores que gerem várias disciplinas
6. [**Painel de Combate**](./combat/README.md) - Interface especializada para a gestão de combates

## Acesso aos Painéis de Controlo

Cada utilizador é automaticamente redirecionado para o painel de controlo correspondente ao seu papel após o início de sessão. O redirecionamento é gerido pela vista `dashboard` no ficheiro `competitions/views/dashboard/base.py`.

## Estrutura Comum dos Painéis de Controlo

Todos os painéis de controlo partilham uma estrutura comum:

- **Cabeçalho**: Apresenta o nome do utilizador, o papel, e dá acesso às definições e ao encerramento de sessão
- **Barra lateral**: Navegação para as diferentes secções do painel de controlo
- **Conteúdo principal**: Apresenta as informações e funcionalidades específicas de cada secção
- **Rodapé**: Informações sobre a versão da aplicação e ligações úteis

## Personalização dos Painéis de Controlo

Os utilizadores podem personalizar certos aspetos do seu painel de controlo:
- Escolha dos widgets apresentados na página inicial
- Ordem de apresentação das informações
- Preferências de notificação

## Funcionalidades Comuns

Todos os painéis de controlo oferecem estas funcionalidades básicas:
- Vista geral com estatísticas-chave
- Notificações e alertas
- Gestão do perfil de utilizador
- Calendário de eventos futuros
- Acesso à documentação

## Suporte Multilingue

Todos os painéis de controlo suportam o multilinguismo e estão disponíveis nos seguintes idiomas:
- Francês (fr) - Idioma predefinido
- Inglês (en)
- Espanhol (es)
- Italiano (it)
- Alemão (de)
- Norueguês (no)
- Japonês (ja)
- Chinês (zh)
- Hindi (hi)
- Árabe (ar)
- Suaíli (sw)
- Amárico (am)
- Zulu (zu)
- Iorubá (yo)
- Português (pt)
- Coreano (ko)

## Conceção Técnica

Os painéis de controlo são implementados utilizando:
- Django para o backend
- HTML/CSS/JavaScript para o frontend
- Bootstrap para o layout responsivo
- Tecnologia AJAX para atualizações dinâmicas

## Documentação Detalhada

Para mais detalhes sobre cada painel de controlo, consulte as ligações acima ou explore as subpastas deste diretório.
