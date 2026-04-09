"""
Management command to translate all 81 tutorials from French to Portuguese.
Updates title_pt, steps_pt, and tip_pt fields via django-modeltranslation.

Usage: python manage.py translate_tutorials_pt
"""
import json

from django.core.management.base import BaseCommand

from apps.competitions.models.tutorials import TutorialSection, Tutorial


# =============================================================================
# TRANSLATION DATA
# =============================================================================

TRANSLATIONS = {
    # =========================================================================
    # Secao 1: Onboarding e Primeiros Passos (7 tutoriais)
    # =========================================================================
    1: {
        'title_pt': 'Onboarding e Primeiros Passos',
        'tutorials': {
            1: {
                'title_pt': 'Criar sua conta e escolher seu papel',
                'steps_pt': [
                    "Acessar o MartialComp : Acesse martialcomp.com e clique em 'Cadastre-se gratis'. Voce tambem pode baixar o aplicativo movel na Play Store ou App Store.",
                    "Preencher o formulario de cadastro : Informe seu sobrenome, nome, e-mail e senha. Voce tambem pode se cadastrar com Google, Facebook ou Apple ID para um acesso simplificado.",
                    "Escolher seu papel principal : Selecione seu papel: Responsavel de Clube, Treinador, Juiz/Arbitro, Praticante ou Responsavel de Federacao. Essa escolha determina seu painel de controle e funcionalidades, mas voce podera adicionar outros papeis posteriormente.",
                    "Confirmar seu e-mail : Verifique sua caixa de entrada e clique no link de confirmacao. Sua conta esta ativa e voce pode acessar seu painel personalizado.",
                ],
                'tip_pt': 'Voce pode ter varios papeis (ex.: treinador E praticante). Alterne entre seus papeis pelo menu lateral a qualquer momento.',
            },
            2: {
                'title_pt': 'Criar seu clube',
                'steps_pt': [
                    "Iniciar o assistente de criacao : No seu painel de controle, clique em 'Criar um clube'. O assistente de configuracao em 4 etapas inicia automaticamente.",
                    "Informacoes gerais : Insira o nome do clube, sigla, endereco completo e dados de contato (telefone, e-mail, site). Adicione seu logotipo em formato PNG ou JPG (tamanho recomendado: 500x500px).",
                    "Escolher as disciplinas : Selecione uma ou mais disciplinas entre as 14+ disponiveis: Karate, Judo, BJJ, Taekwondo, MMA, Kung Fu, Aikido, Kendo, Muay Thai, Boxe, Capoeira, etc.",
                    "Personalizar seu subdominio : Escolha seu endereco unico: seu-clube.martialcomp.com. Este sera o endereco publico do seu clube, acessivel para todos.",
                    "Configurar opcoes : Defina os horarios de funcionamento, adicione uma descricao e fotos do seu dojo. Ative ou desative o cadastro online de praticantes.",
                ],
                'tip_pt': 'Seu clube e criado com o plano Gratuito (ate 10 membros). Todas as funcionalidades estao disponiveis desde o inicio. Faca upgrade para Premium quando ultrapassar 10 membros.',
            },
            3: {
                'title_pt': 'Criar sua federacao',
                'steps_pt': [
                    "Solicitar a criacao : Selecione o papel 'Responsavel de Federacao' durante o cadastro ou adicione-o nas configuracoes. Preencha o formulario de criacao com as informacoes oficiais da sua federacao.",
                    "Informacoes oficiais : Insira o nome completo, sigla, pais, disciplinas abrangidas, numero de registro oficial e dados de contato.",
                    "Configurar o site publico : Personalize sua pagina publica: banner, logotipo, cores, descricao, galeria de fotos e links para suas redes sociais.",
                    "Definir a estrutura : Configure suas ligas regionais, se aplicavel, defina as categorias de filiacao para os clubes e as tarifas de contribuicoes.",
                ],
                'tip_pt': 'As federacoes possuem um espaco de administracao ampliado para supervisionar todos os clubes filiados, competicoes e graduacoes.',
            },
            4: {
                'title_pt': 'Configurar seu perfil de treinador',
                'steps_pt': [
                    "Acessar o perfil de treinador : No menu lateral, clique em 'Meu perfil de treinador'. Se voce ainda nao tem o papel de treinador, adicione-o em Configuracoes > Meus papeis.",
                    "Inserir suas qualificacoes : Adicione seus diplomas (CREF, graduacoes, etc.), suas graduacoes em cada disciplina e seus anos de experiencia.",
                    "Definir suas disciplinas : Selecione as disciplinas que voce ensina e seu nivel de especializacao em cada uma (iniciantes, avancados, competicao).",
                    "Definir sua disponibilidade : Indique suas faixas horarias semanais de ensino. Essas informacoes serao visiveis para os clubes que procuram treinadores.",
                ],
                'tip_pt': 'Um perfil de treinador completo com foto e certificacoes aumenta significativamente sua visibilidade junto aos clubes.',
            },
            5: {
                'title_pt': 'Configurar seu perfil de juiz',
                'steps_pt': [
                    "Ativar o papel de juiz : Em Configuracoes > Meus papeis, ative o papel 'Juiz / Arbitro'. Insira seu numero de licenca de juiz, se aplicavel.",
                    "Adicionar suas qualificacoes : Indique seu nivel de juiz (regional, nacional, internacional), as disciplinas para as quais voce esta qualificado e suas certificacoes.",
                    "Definir suas especialidades : Kata/tecnicas, combate, pontuacao artistica... Cada especialidade o habilita para as competicoes correspondentes.",
                    "Informar sua disponibilidade : Indique suas zonas geograficas e periodos de disponibilidade para competicoes.",
                ],
                'tip_pt': 'Os organizadores de competicoes poderao encontra-lo e convida-lo diretamente com base em suas qualificacoes e disponibilidade.',
            },
            6: {
                'title_pt': 'Configurar seu perfil de praticante',
                'steps_pt': [
                    "Preencher as informacoes pessoais : Insira sua data de nascimento, sexo, peso (para categorias de competicao), altura e foto de perfil.",
                    "Adicionar sua graduacao atual : Indique sua disciplina principal, sua graduacao atual (faixa), a data de obtencao e o organismo que a concedeu.",
                    "Inserir sua licenca : Adicione seu numero de licenca federativa, a data de validade e o atestado medico vigente.",
                    "Contatos de emergencia : Adicione pelo menos um contato de emergencia (obrigatorio para competicoes): nome, telefone, parentesco.",
                ],
                'tip_pt': 'Um perfil completo e necessario para se inscrever em competicoes. O peso e a graduacao determinam automaticamente sua categoria.',
            },
            7: {
                'title_pt': 'Entender o painel de controle e a navegacao',
                'steps_pt': [
                    "O painel de controle : Seu painel exibe um resumo personalizado: proximos eventos, mensagens recentes, estatisticas rapidas e atalhos para suas acoes frequentes.",
                    "A barra lateral : O menu lateral da acesso a todas as secoes: Membros, Competicoes, Graduacoes, Financas, Calendario, Configuracoes. Ele se adapta ao seu papel ativo.",
                    "Alternar papel : Se voce tem varios papeis (ex.: treinador + praticante), clique no seu avatar no canto superior direito para alternar. O painel e o menu se adaptam automaticamente.",
                    "Notificacoes e mensagens : O icone de sino no canto superior direito mostra suas notificacoes: inscricoes, resultados, mensagens. Configure suas preferencias de notificacao nas configuracoes.",
                    "Busca global : Use a barra de busca para encontrar rapidamente um praticante, clube, competicao ou evento.",
                ],
                'tip_pt': 'Personalize seu painel fixando seus widgets favoritos. O atalho de teclado Ctrl+K abre a busca rapida.',
            },
        },
    },

    # =========================================================================
    # Secao 2: Gestao do Clube (10 tutoriais)
    # =========================================================================
    2: {
        'title_pt': 'Gestao do Clube',
        'tutorials': {
            1: {
                'title_pt': 'Adicionar praticantes manualmente',
                'steps_pt': [
                    "Abrir o formulario de cadastro : Em Membros > Adicionar um praticante, preencha o formulario: sobrenome, nome, data de nascimento, sexo, e-mail e telefone.",
                    "Informacoes adicionais : Adicione a graduacao atual, o numero de licenca, a foto de identificacao (opcional) e o atestado medico.",
                    "Atribuir a um grupo : Atribua o praticante a um ou mais grupos de treino (ex.: Karate Adultos Avancado, Judo Criancas Iniciante).",
                    "Enviar o convite : Marque 'Enviar um e-mail de convite' para que o praticante possa criar sua propria conta e acessar seu perfil online.",
                ],
                'tip_pt': 'O praticante recebera um e-mail com um link para completar seu cadastro e baixar o aplicativo movel.',
            },
            2: {
                'title_pt': 'Importacao em massa de praticantes (CSV/Excel)',
                'steps_pt': [
                    "Baixar o modelo : Em Membros > Importar, baixe o modelo CSV ou Excel. O arquivo contem colunas obrigatorias: Sobrenome, Nome, Data_nascimento, E-mail, e colunas opcionais: Graduacao, Licenca, Telefone.",
                    "Preencher o arquivo : Complete o arquivo com os dados dos seus praticantes. Respeite os formatos: datas em DD/MM/AAAA, graduacoes como texto (ex.: 'Faixa verde', '2o Dan').",
                    "Carregar e mapear colunas : Importe o arquivo. A interface de mapeamento permite associar cada coluna do seu arquivo com os campos do MartialComp. Verifique o mapeamento.",
                    "Validar e corrigir : O MartialComp detecta erros (duplicados, formatos invalidos). Corrija as linhas com erros ou pule-as. Confirme a importacao.",
                ],
                'tip_pt': 'Voce pode importar ate 500 praticantes em uma unica operacao. A importacao detecta automaticamente duplicados por e-mail ou sobrenome + nome + data de nascimento.',
            },
            3: {
                'title_pt': 'Gerenciar as fichas dos praticantes',
                'steps_pt': [
                    "Acessar a ficha : Na lista de membros, clique no nome de um praticante para abrir sua ficha completa.",
                    "Ver os detalhes : A ficha exibe: informacoes pessoais, historico de graduacoes, competicoes realizadas, frequencia e mensalidades.",
                    "Editar as informacoes : Clique em 'Editar' para atualizar os dados. As alteracoes sao registradas no historico.",
                    "Acoes rapidas : A partir da ficha voce pode: inscrever em uma competicao, atribuir uma graduacao, enviar uma mensagem, gerar um certificado.",
                ],
                'tip_pt': 'Use os filtros avancados (graduacao, idade, licenca vigente, mensalidade paga) para encontrar rapidamente um praticante.',
            },
            4: {
                'title_pt': 'Criar uma conta de usuario para um praticante',
                'steps_pt': [
                    "Acessar a ficha do praticante : Abra a ficha do praticante correspondente na lista de membros.",
                    "Vincular a uma conta : Clique em 'Criar uma conta de usuario'. Um e-mail de convite sera enviado ao praticante com um link para criar sua senha.",
                    "Definir permissoes : Escolha o que o praticante pode fazer: ver seus resultados, inscrever-se em competicoes, ver o calendario, pagar online.",
                ],
                'tip_pt': 'Praticantes menores de idade podem ter uma conta vinculada a de um responsavel atraves da funcao Grupo Familiar.',
            },
            5: {
                'title_pt': 'Gerenciar papeis e permissoes do clube',
                'steps_pt': [
                    "Acessar a gestao de papeis : Em Configuracoes > Papeis e permissoes, visualize os papeis disponiveis: Administrador, Secretario, Tesoureiro, Treinador, Membro.",
                    "Atribuir um papel : Selecione um membro e atribua-lhe um papel. Cada papel concede acesso a funcionalidades especificas.",
                    "Personalizar permissoes : Para cada papel, defina os direitos: somente leitura, edicao, exclusao, acesso a financas, gestao de inscricoes.",
                    "Auditar acessos : Consulte o registro de atividades para ver quem fez o que e quando na administracao do clube.",
                ],
                'tip_pt': 'O papel de Administrador possui todos os direitos. Crie um papel de Secretario com acesso a membros e calendario, mas sem acesso a financas.',
            },
            6: {
                'title_pt': 'Acompanhamento de frequencia / Check-in',
                'steps_pt': [
                    "Criar uma sessao : Em Frequencia > Nova sessao, selecione o grupo de treino, a data e o horario da aula.",
                    "Registrar por lista : Exiba a lista de membros do grupo e marque os presentes. O registro e feito com um unico toque no celular.",
                    "Registrar por codigo QR : Exiba o codigo QR da sessao. Os praticantes escaneiam com o celular ao chegar no dojo.",
                    "Ver estatisticas : Visualize as taxas de frequencia por praticante, grupo e periodo. Identifique as ausencias recorrentes.",
                ],
                'tip_pt': 'O check-in por codigo QR e o metodo mais rapido para grupos grandes. O codigo e renovado a cada sessao para evitar fraudes.',
            },
            7: {
                'title_pt': 'Gerenciar os programas de treino',
                'steps_pt': [
                    "Criar um programa : Em Programas > Novo, defina o nome, a disciplina, o nivel (iniciante, intermediario, avancado) e a duracao do ciclo.",
                    "Planejar as sessoes : Adicione as faixas horarias semanais: dia, hora de inicio, hora de termino, sala/tatame, treinador responsavel.",
                    "Definir os conteudos : Para cada sessao, adicione um plano: aquecimento, trabalho tecnico, sparring/randori, volta a calma. Anexe arquivos ou videos.",
                    "Publicar e notificar : Publique o programa. Os praticantes do grupo recebem uma notificacao com o programa completo.",
                ],
                'tip_pt': 'Duplique um programa existente para criar rapidamente um novo ciclo com variacoes.',
            },
            8: {
                'title_pt': 'Gerar e utilizar os codigos QR do clube',
                'steps_pt': [
                    "Gerar o codigo QR do clube : Em Configuracoes > Codigos QR, gere o codigo QR do seu clube. Permite que visitantes acessem diretamente sua pagina publica.",
                    "Codigos QR especiais : Gere codigos QR para: cadastro online, check-in de sessao, pagina de evento ou link para o aplicativo movel.",
                    "Imprimir e exibir : Baixe os codigos QR em alta resolucao para impressao. Formatos disponiveis: PNG, SVG, PDF (A4 ou cartao de visita).",
                    "Monitorar estatisticas : Visualize o numero de leituras por codigo QR, por dia e por tipo. Identifique os codigos QR mais eficazes.",
                ],
                'tip_pt': 'Exiba o codigo QR de cadastro na entrada do seu dojo. Cada leitura e um cliente em potencial!',
            },
            9: {
                'title_pt': 'Solicitar a filiacao a federacao',
                'steps_pt': [
                    "Encontrar sua federacao : Em Clube > Filiacao, busque sua federacao por nome, disciplina ou pais.",
                    "Enviar a solicitacao : Preencha o formulario de filiacao: informacoes do clube, numero de registro, documentos comprobatorios (estatuto, seguro, etc.).",
                    "Acompanhar o status : Sua solicitacao passa por etapas: Enviada > Em analise > Aprovada/Recusada. Voce recebe notificacoes a cada etapa.",
                    "Renovar a cada temporada : A filiacao e por temporada. Um lembrete automatico e enviado 30 dias antes do vencimento.",
                ],
                'tip_pt': 'A filiacao da acesso as competicoes oficiais da federacao e a gestao centralizada de licencas.',
            },
            10: {
                'title_pt': 'Gerenciar as transferencias de praticantes',
                'steps_pt': [
                    "Iniciar uma transferencia : Na ficha de um praticante, clique em 'Solicitar uma transferencia'. Selecione o clube de destino e o motivo da transferencia.",
                    "Processo de validacao : O clube de destino recebe a solicitacao e pode aceita-la ou recusa-la. Se houver uma federacao envolvida, ela tambem deve validar.",
                    "Transferencia efetivada : Uma vez validada, o praticante e transferido automaticamente com sua graduacao e historico de competicoes.",
                    "Ver o historico : O historico de transferencias e visivel na ficha do praticante e nos relatorios do clube.",
                ],
                'tip_pt': 'Algumas federacoes impoem periodos de transferencia (janelas de transferencia). O MartialComp respeita automaticamente essas regras.',
            },
        },
    },

    # =========================================================================
    # Secao 3: Competicoes - Criacao e Configuracao (6 tutoriais)
    # =========================================================================
    3: {
        'title_pt': 'Competicoes - Criacao e Configuracao',
        'tutorials': {
            1: {
                'title_pt': 'Criar uma competicao individual',
                'steps_pt': [
                    "Iniciar a criacao : Em Competicoes > Criar, escolha o tipo 'Individual'. Insira o nome, a(s) disciplina(s), as datas e o local.",
                    "Definir o formato : Escolha o formato: Combate (kumite, randori, sparring), Tecnico (kata, poomsae, formas) ou Misto (ambos).",
                    "Configurar as categorias : Defina as categorias por sexo, faixa etaria, peso e/ou graduacao. O MartialComp oferece modelos de categorias padrao por disciplina.",
                    "Opcoes e publicacao : Ative as opcoes desejadas: inscricao online, pagamento, transmissao ao vivo, resultados publicos. Publique a competicao.",
                ],
                'tip_pt': 'Use os modelos de categorias (WKF, IJF, ITF...) para economizar tempo. Voce pode personaliza-los apos a criacao.',
            },
            2: {
                'title_pt': 'Criar uma competicao por equipes (Sincro/Song Luyen)',
                'steps_pt': [
                    "Escolher o modo equipe : Durante a criacao, selecione o tipo 'Equipe'. Defina o numero minimo e maximo de membros por equipe.",
                    "Configurar o formato de equipe : Escolha o formato: Sincronizacao (kata/poomsae de equipe), Song Luyen (combate predefinido para dois) ou Combate por equipes (revezamento).",
                    "Definir a composicao : Especifique os papeis dentro da equipe: numero de titulares, numero de reservas, se composicoes mistas sao permitidas ou nao.",
                    "Criterios de pontuacao de equipe : Para a pontuacao tecnica, defina se os juizes avaliam a equipe como um todo ou cada membro individualmente.",
                ],
                'tip_pt': 'O modo Sincro permite a pontuacao com criterios de sincronizacao especificos (timing, alinhamento, expressao compartilhada).',
            },
            3: {
                'title_pt': 'Configurar as categorias de competicao',
                'steps_pt': [
                    "Acessar a gestao de categorias : Na competicao criada, va ate a aba Categorias. Clique em 'Adicionar uma categoria'.",
                    "Definir os criterios : Para cada categoria, defina: sexo (M/F/Misto), faixa etaria (ex.: 12-14 anos), faixa de peso (ex.: -60kg), graduacao minima/maxima.",
                    "Nomear a categoria : De um nome claro: 'Cadete Masculino -52kg' ou 'Kata Adulto Feminino Avancado'. O MartialComp gera nomes automaticos se preferir.",
                    "Ordenar as categorias : Reordene as categorias arrastando e soltando para definir a ordem de exibicao no dia da competicao.",
                ],
                'tip_pt': 'Importe as categorias de uma competicao anterior para economizar tempo. Use a opcao \'Duplicacao Inteligente\' para criar variantes.',
            },
            4: {
                'title_pt': 'Duplicar uma competicao existente',
                'steps_pt': [
                    "Encontrar a competicao de origem : Em Competicoes > Historico, encontre a competicao que deseja duplicar.",
                    "Iniciar a duplicacao : Clique nos 3 pontos > Duplicar. Escolha o que copiar: categorias, regulamento, configuracao, tarifas.",
                    "Ajustar a configuracao : Modifique as datas, o local e os parametros necessarios. As categorias e o regulamento sao copiados de forma identica.",
                ],
                'tip_pt': 'Ideal para competicoes anuais recorrentes. Duplique a edicao anterior e simplesmente atualize as datas.',
            },
            5: {
                'title_pt': 'Configurar as opcoes de visibilidade',
                'steps_pt': [
                    "Acessar a configuracao de visibilidade : Na competicao, va em Configuracoes > Visibilidade e compartilhamento.",
                    "Inscricoes online : Ative/desative as inscricoes publicas. Defina as datas de abertura e fechamento das inscricoes.",
                    "Resultados e classificacoes : Escolha se os resultados sao publicos em tempo real, publicados apos a validacao ou privados (somente organizador).",
                    "Transmissao ao vivo : Ative o modo de transmissao e adicione o link do YouTube/Twitch/Facebook Live para exibi-lo na pagina publica.",
                ],
                'tip_pt': 'Os resultados ao vivo atraem espectadores para sua pagina e aumentam a visibilidade do seu clube ou federacao.',
            },
            6: {
                'title_pt': 'Configurar as regras de combate',
                'steps_pt': [
                    "Escolher um regulamento : Selecione um regulamento pre-configurado (WKF, IJF, ITF, IBJJF, etc.) ou crie um personalizado.",
                    "Definir a pontuacao : Configure as acoes e seus pontos: Yuko (1pt), Waza-ari (2pts), Ippon (3pts), etc. Adicione as penalidades (Shido, Hansoku, etc.).",
                    "Configurar os rounds : Defina a duracao dos rounds, o numero de rounds, as pausas e as condicoes de vitoria (pontos, Ippon, desistencia).",
                    "Regras especiais : Configure as regras especificas: Golden Score (tempo extra), Hantei (decisao dos juizes), finalizacao antecipada por diferenca de pontos.",
                ],
                'tip_pt': 'Salve seus regulamentos personalizados como modelos para reutiliza-los em futuras competicoes.',
            },
        },
    },

    # =========================================================================
    # Secao 4: Inscricoes e Equipes (7 tutoriais)
    # =========================================================================
    4: {
        'title_pt': 'Inscricoes e Equipes',
        'tutorials': {
            1: {
                'title_pt': 'Inscrever praticantes em uma competicao',
                'steps_pt': [
                    "Encontrar a competicao : Em Competicoes > Abertas para inscricoes, encontre a competicao desejada e clique em 'Inscrever'.",
                    "Selecionar os praticantes : A lista dos seus membros e exibida. Selecione um ou mais praticantes. O MartialComp indica automaticamente as categorias elegiveis para cada um.",
                    "Confirmar as categorias : Para cada praticante, confirme ou altere a categoria proposta. O sistema verifica se o peso, a idade e a graduacao correspondem.",
                    "Validar e pagar : Confirme as inscricoes. Se a competicao exige pagamento, efetue o pagamento de todas as inscricoes.",
                ],
                'tip_pt': 'Os praticantes com perfil incompleto (peso ausente, licenca vencida) serao sinalizados com um alerta vermelho.',
            },
            2: {
                'title_pt': 'Inscricao em massa por formulario',
                'steps_pt': [
                    "Acessar o modo em massa : Na tela de inscricao, clique em 'Inscricao em massa'. Selecione a categoria de destino.",
                    "Selecionar o grupo : Filtre por grupo de treino, graduacao ou idade. Selecione os praticantes elegiveis com um unico clique.",
                    "Verificar e ajustar : A tela de verificacao exibe cada praticante com sua categoria. Corrija os erros, se houver.",
                    "Confirmar o lote : Valide todas as inscricoes em uma unica operacao. Um resumo e enviado por e-mail.",
                ],
                'tip_pt': 'A inscricao em massa e ideal para clubes que inscrevem 10+ praticantes na mesma competicao.',
            },
            3: {
                'title_pt': 'Criar e gerenciar equipes',
                'steps_pt': [
                    "Criar uma equipe : Na competicao, clique em 'Inscrever uma equipe'. De um nome a equipe e selecione a categoria.",
                    "Adicionar membros : Adicione membros da equipe a partir da sua lista de praticantes. Respeite os numeros minimos e maximos definidos.",
                    "Definir titulares e reservas : Designe titulares e reservas arrastando e soltando. A ordem de apresentacao pode ser definida aqui.",
                    "Validar a equipe : Verifique a conformidade da equipe (numero de membros, categorias individuais) e confirme a inscricao.",
                ],
                'tip_pt': 'Nas competicoes por equipes, o nome da equipe aparece nos placares e nos resultados oficiais.',
            },
            4: {
                'title_pt': 'Alterar a categoria de uma equipe',
                'steps_pt': [
                    "Acessar a equipe : Nas suas inscricoes, encontre a equipe a modificar e clique em 'Editar'.",
                    "Alterar a categoria : Selecione a nova categoria no menu suspenso. O sistema verifica se a equipe atende aos criterios.",
                    "Confirmar a alteracao : Valide. Se a competicao tem tarifas de inscricao diferentes por categoria, o ajuste e automatico.",
                ],
                'tip_pt': 'A alteracao de categoria so e possivel enquanto as inscricoes estiverem abertas.',
            },
            5: {
                'title_pt': 'Solicitar uma alianca (fusao entre clubes)',
                'steps_pt': [
                    "Identificar a necessidade : Seu clube nao tem membros suficientes para formar uma equipe completa? A alianca permite unir equipes de clubes diferentes.",
                    "Criar a solicitacao de alianca : Na equipe incompleta, clique em 'Propor uma alianca'. Selecione o clube parceiro e as vagas a preencher.",
                    "Enviar a proposta : O clube parceiro recebe a solicitacao com os detalhes: competicao, categoria, vagas disponiveis, condicoes.",
                    "Finalizar a alianca : Uma vez aceita, a equipe fusionada aparece com os membros de ambos os clubes. A equipe leva um nome que combina os dois clubes.",
                ],
                'tip_pt': 'A alianca esta sujeita a aprovacao do organizador da competicao e, se aplicavel, da federacao.',
            },
            6: {
                'title_pt': 'Aceitar/recusar uma solicitacao de alianca',
                'steps_pt': [
                    "Receber a notificacao : Voce recebe uma notificacao de solicitacao de alianca. Clique para ver os detalhes.",
                    "Analisar a proposta : Verifique: o clube solicitante, a competicao, a categoria, as vagas a preencher e as condicoes propostas.",
                    "Aceitar ou recusar : Clique em 'Aceitar' para validar a alianca e selecionar seus membros, ou 'Recusar' com uma mensagem explicativa.",
                ],
                'tip_pt': 'Voce pode propor uma contraproposta modificando as condicoes antes de aceitar.',
            },
            7: {
                'title_pt': 'Gerenciar as inscricoes recebidas (aprovacao)',
                'steps_pt': [
                    "Acessar o painel de inscricoes : Na competicao, va ate a aba Inscricoes. Visualize as inscricoes por status: Pendente, Aprovada, Recusada.",
                    "Analisar e aprovar : Clique em uma inscricao para verificar as informacoes do praticante. Aprove individualmente ou em lote.",
                    "Recusar com motivo : Em caso de recusa, selecione um motivo: categoria incorreta, licenca invalida, inscricao tardia, etc.",
                    "Exportar a lista : Exporte a lista de inscritos validados em CSV ou PDF para a pesagem e a gestao no dia da competicao.",
                ],
                'tip_pt': 'Ative a aprovacao automatica se voce nao quiser validar manualmente cada inscricao.',
            },
        },
    },

    # =========================================================================
    # Secao 5: Dia de Competicao - Combate (8 tutoriais)
    # =========================================================================
    5: {
        'title_pt': 'Dia de Competicao - Combate',
        'tutorials': {
            1: {
                'title_pt': 'Gerar as chaves automaticamente',
                'steps_pt': [
                    "Acessar a gestao de chaves : Na competicao, va em Chaves > Gerar automaticamente. Selecione as categorias a processar.",
                    "Configurar a distribuicao : Defina: numero de competidores por chave, separacao de membros do mesmo clube, cabecas de chave manuais (opcional).",
                    "Gerar e verificar : Clique em 'Gerar'. O MartialComp distribui os competidores evitando confrontos entre membros do mesmo clube na primeira rodada.",
                    "Ajustar manualmente : Se necessario, mova competidores entre chaves arrastando e soltando. O sistema verifica conflitos em tempo real.",
                ],
                'tip_pt': 'O algoritmo de distribuicao garante equidade separando clubes e equilibrando niveis de habilidade entre as chaves.',
            },
            2: {
                'title_pt': 'Organizar e reorganizar as chaves',
                'steps_pt': [
                    "Visao geral das chaves : A tela de chaves exibe todas as categorias com o numero de competidores, chaves e status (rascunho, validado, em andamento).",
                    "Editar uma chave : Clique em uma chave para ver os competidores. Use arrastar e soltar para mover um competidor para outra chave.",
                    "Gerenciar ausencias : Marque um competidor como ausente ou desistente. O sistema recalcula automaticamente os confrontos e classificacoes.",
                    "Validar as chaves : Uma vez satisfeito, valide as chaves. Essa acao gera automaticamente a tabela de confrontos.",
                ],
                'tip_pt': 'Valide as chaves categoria por categoria para iniciar os combates das primeiras categorias enquanto finaliza as demais.',
            },
            3: {
                'title_pt': 'Planejar o cronograma de combates',
                'steps_pt': [
                    "Definir as areas de combate : Em Cronograma > Areas, defina o numero de tatames/ringues disponiveis e seus nomes (Tatame 1, Ringue A, etc.).",
                    "Atribuir faixas horarias : Arraste as categorias sobre as areas e as faixas horarias. O MartialComp calcula automaticamente a duracao estimada.",
                    "Detectar conflitos : O sistema detecta conflitos: um competidor inscrito em 2 categorias ao mesmo tempo. Use os alertas para ajustar.",
                    "Publicar o cronograma : Publique o cronograma. Competidores, treinadores e juizes recebem uma notificacao com seus horarios de participacao.",
                ],
                'tip_pt': 'Planeje 20% de tempo extra por categoria para gerenciar os inevitaveis atrasos.',
            },
            4: {
                'title_pt': 'Usar a interface de combate (pontuacao ao vivo)',
                'steps_pt': [
                    "Conectar-se a area : No seu tablet ou celular, abra o MartialComp e selecione sua area de combate designada. Insira seu PIN de juiz.",
                    "A interface de pontuacao : A tela exibe: os 2 competidores (vermelho/azul), botoes de acao (pontos, penalidades), o cronometro e a pontuacao atual.",
                    "Atribuir pontos : Pressione os botoes de pontuacao: Yuko (+1), Waza-ari (+2), Ippon (+3) para o competidor vermelho ou azul. Os pontos sao atualizados em tempo real.",
                    "Gerenciar penalidades : Pressione Penalidade para aplicar uma advertencia (Shido) ou desqualificacao (Hansoku). As penalidades sao cumulativas.",
                    "Finalizar o combate : O cronometro para automaticamente. Valide o resultado (vitoria por pontos, Ippon, desistencia). A classificacao e atualizada instantaneamente.",
                ],
                'tip_pt': 'A interface e otimizada para tablets no modo paisagem. Os botoes sao intencionalmente grandes para uso rapido e sem erros.',
            },
            5: {
                'title_pt': 'Modo Quiosque multi-tatame',
                'steps_pt': [
                    "Ativar o modo Quiosque : Em Configuracoes > Modo Quiosque, ative o modo e defina um codigo PIN para cada area de combate.",
                    "Configurar cada tablet : Em cada tablet da area, faca login e selecione a area correspondente. Insira o PIN para bloquear a tela nessa area.",
                    "Gestao independente : Cada area funciona de forma autonoma: pontuacao, cronometro, exibicao. O placar central e atualizado em tempo real.",
                    "Tela para espectadores : Conecte uma tela adicional no modo 'Espectador' para exibir a pontuacao em grande formato, visivel das arquibancadas.",
                ],
                'tip_pt': 'O modo Quiosque impede que os juizes naveguem acidentalmente para fora da interface de pontuacao.',
            },
            6: {
                'title_pt': 'Acompanhar as classificacoes ao vivo',
                'steps_pt': [
                    "Painel ao vivo : A tela de acompanhamento exibe em tempo real: combates em andamento por area, classificacoes das chaves, avanco para as fases finais.",
                    "Filtrar por categoria : Selecione uma categoria para ver os detalhes: chaves concluidas, em andamento e pendentes, com classificacoes provisorias.",
                    "Notificacoes automaticas : O sistema notifica automaticamente os treinadores quando seus competidores devem se apresentar na area de combate.",
                ],
                'tip_pt': 'Exiba o painel em uma tela grande na area de recepcao para que todos os participantes possam acompanhar o andamento.',
            },
            7: {
                'title_pt': 'Gerar as fases finais (semifinais/finais)',
                'steps_pt': [
                    "Chaves concluidas : Uma vez concluidas todas as chaves de uma categoria, o sistema calcula os classificados conforme as regras definidas (1o e 2o por chave, etc.).",
                    "Gerar o chaveamento : Clique em 'Gerar fases finais'. O chaveamento eliminatorio (quartas, semifinais, final, disputa pelo bronze) e gerado automaticamente.",
                    "Gerenciar repescagens : Se as regras preverem, as repescagens sao geradas automaticamente com os perdedores das semifinais.",
                    "Iniciar as finais : Os combates das fases finais aparecem no cronograma. A pontuacao funciona da mesma forma que para as chaves.",
                ],
                'tip_pt': 'O chaveamento eliminatorio e gerado automaticamente evitando, quando possivel, confrontos entre competidores do mesmo clube.',
            },
            8: {
                'title_pt': 'Gerenciar a cerimonia do podio',
                'steps_pt': [
                    "Acessar o podio : Na categoria concluida, clique em 'Podio'. A classificacao final e exibida: Ouro, Prata, Bronze (e possivelmente 2 bronzes).",
                    "Exibicao progressiva : Use o modo 'Cerimonia' para uma exibicao progressiva: 3o, depois 2o, depois 1o, com animacoes e efeitos sonoros.",
                    "Projetar em tela grande : Conecte o modo Apresentacao a um projetor para uma exibicao espetacular durante a entrega das medalhas.",
                    "Compartilhar resultados : Os podios sao publicados automaticamente na pagina da competicao e podem ser compartilhados nas redes sociais.",
                ],
                'tip_pt': 'Tire uma foto do podio e adicione-a a competicao para enriquecer a galeria e as redes sociais.',
            },
        },
    },

    # =========================================================================
    # Secao 6: Pontuacao Tecnica (6 tutoriais)
    # =========================================================================
    6: {
        'title_pt': 'Pontuacao Tecnica',
        'tutorials': {
            1: {
                'title_pt': 'Configurar os criterios de pontuacao',
                'steps_pt': [
                    "Acessar os criterios : Na competicao, va em Pontuacao > Criterios. Selecione um modelo ou crie seus proprios criterios.",
                    "Definir os criterios : Adicione criterios de avaliacao: Tecnica (posicoes, transicoes), Potencia (kime, dinamica), Ritmo (tempo, fluidez), Expressao (zanshin, espirito).",
                    "Atribuir pesos : Defina o peso de cada criterio: ex.: Tecnica 40%, Potencia 25%, Ritmo 20%, Expressao 15%. O total deve ser 100%.",
                    "Definir a escala : Escolha a escala de pontuacao: 1-5, 1-10, 5.0-10.0 ou personalizada. Defina o incremento (0.1, 0.5 ou 1).",
                ],
                'tip_pt': 'Os modelos WKF e WTF estao pre-configurados. Personalize-os conforme suas necessidades especificas.',
            },
            2: {
                'title_pt': 'Atribuir juizes as categorias',
                'steps_pt': [
                    "Abrir o painel de atribuicao : Em Pontuacao > Juizes, visualize a lista de juizes cadastrados e as categorias a serem cobertas.",
                    "Atribuir por categoria : Arraste os juizes para as categorias. Defina o numero de juizes por categoria (geralmente 5 ou 7).",
                    "Verificacao de neutralidade : O MartialComp verifica automaticamente os conflitos de interesse: um juiz nao pode avaliar um competidor do seu proprio clube.",
                    "Gerenciar as rotacoes : Planeje as rotacoes de juizes entre categorias para prevenir a fadiga e manter a equidade.",
                ],
                'tip_pt': 'O sistema de deteccao de vies analisa as diferencas de pontuacao entre juizes e alerta se um juiz pontua sistematicamente muito alto ou muito baixo.',
            },
            3: {
                'title_pt': 'Usar a folha de pontuacao tecnica',
                'steps_pt': [
                    "Fazer login como juiz : No seu tablet, faca login com sua conta de juiz. Selecione a categoria atribuida.",
                    "Interface de pontuacao : A tela exibe o competidor atual, os criterios de avaliacao e o teclado numerico. Cada criterio tem seu proprio controle deslizante ou teclado.",
                    "Avaliar por rodada : Para cada competidor, insira sua pontuacao para cada criterio. Valide sua avaliacao antes de passar para o proximo.",
                    "Salvar : Sua avaliacao e salva instantaneamente. Voce pode modificar suas pontuacoes enquanto a rodada nao tiver sido bloqueada pelo organizador.",
                ],
                'tip_pt': 'A interface digital e otimizada para entrada rapida em tablets. Um unico toque para cada pontuacao.',
            },
            4: {
                'title_pt': 'Pontuacao tecnica de equipe (Sincro)',
                'steps_pt': [
                    "Entender o modo equipe : Na pontuacao Sincro, criterios adicionais aparecem: Sincronizacao, Alinhamento Espacial, Expressao Compartilhada.",
                    "Avaliar a equipe como um todo : Se configurado dessa forma, avalie a equipe como um todo para cada criterio, incluindo a sincronizacao.",
                    "Avaliar individualmente + equipe : Se configurado para avaliacao mista, avalie cada membro individualmente E DEPOIS adicione uma pontuacao de equipe para a sincronizacao.",
                ],
                'tip_pt': 'No modo Sincro, o criterio de sincronizacao representa tipicamente 20-30% da pontuacao total.',
            },
            5: {
                'title_pt': 'Bloquear e publicar as pontuacoes',
                'steps_pt': [
                    "Verificar as pontuacoes : No painel do organizador, visualize as pontuacoes de todos os juizes para cada competidor. Identifique as diferencas suspeitas.",
                    "Bloquear uma rodada : Clique em 'Bloquear' para impedir qualquer modificacao. O calculo final (eliminar pontuacao mais alta/mais baixa, media) e realizado.",
                    "Publicar os resultados : Publique as classificacoes. As pontuacoes detalhadas por juiz podem ser ocultadas ou exibidas conforme sua configuracao.",
                    "Modo teste / reinicio : Antes da competicao, use o modo teste para verificar o sistema. O reinicio apaga todas as pontuacoes de teste.",
                ],
                'tip_pt': 'O bloqueio rodada por rodada permite publicar resultados progressivamente enquanto a competicao continua.',
            },
            6: {
                'title_pt': 'Ver as classificacoes provisorias',
                'steps_pt': [
                    "Acessar as classificacoes : Na aba Classificacoes, visualize as classificacoes em tempo real com as pontuacoes por criterio e a pontuacao final.",
                    "Ordenar e filtrar : Ordene por pontuacao total ou por criterio especifico. Filtre por chave ou todos os competidores.",
                    "Estatisticas dos juizes : Visualize as estatisticas: media por juiz, desvio padrao, deteccao de vies. Uma ferramenta essencial para a equidade.",
                ],
                'tip_pt': 'A classificacao provisoria so e visivel para organizadores e juizes. Ela e publicada para os competidores somente apos o bloqueio.',
            },
        },
    },

    # =========================================================================
    # Secao 7: Resultados e Palmares (4 tutoriais)
    # =========================================================================
    7: {
        'title_pt': 'Resultados e Palmares',
        'tutorials': {
            1: {
                'title_pt': 'Ver os resultados da competicao',
                'steps_pt': [
                    "Encontrar a competicao : No menu Competicoes ou na pagina publica, selecione a competicao desejada.",
                    "Consultar os resultados : Os resultados estao organizados por categoria. Para cada categoria: podio, classificacao completa e detalhes das pontuacoes.",
                    "Detalhes do combate : Clique em um combate para ver os detalhes: pontuacao por round, penalidades, cronometro e possivelmente o video do combate.",
                ],
                'tip_pt': 'Os resultados publicos sao acessiveis sem conta MartialComp atraves do link da competicao.',
            },
            2: {
                'title_pt': 'Publicar e compartilhar os resultados',
                'steps_pt': [
                    "Validar os resultados : No painel do organizador, revise os resultados de cada categoria. Clique em 'Validar e publicar'.",
                    "Gerar o link publico : Um link permanente para a pagina de resultados e gerado. Copie-o para compartilhar.",
                    "Compartilhar nas redes sociais : Use os botoes de compartilhamento integrados para publicar no Facebook, Instagram, Twitter. Os podios geram automaticamente uma imagem.",
                    "Codigo QR de resultados : Gere um codigo QR de resultados para exibir no local da competicao para os espectadores.",
                ],
                'tip_pt': 'A imagem automatica do podio esta formatada para Instagram Stories (9:16) e Facebook (16:9).',
            },
            3: {
                'title_pt': 'Exportar os resultados (CSV/PDF)',
                'steps_pt': [
                    "Acessar a exportacao : Em Resultados > Exportar, escolha o formato: CSV (dados brutos), PDF (relatorio formatado) ou Excel.",
                    "Escolher o conteudo : Selecione: Classificacao geral, Somente podios, Detalhe por categoria, Relatorio de medalhas por clube ou Tudo.",
                    "Personalizar o PDF : Para o PDF, escolha o modelo: relatorio oficial (com logotipo da federacao), relatorio simples ou diplomas.",
                ],
                'tip_pt': 'O relatorio de medalhas por clube e particularmente util para federacoes e patrocinadores.',
            },
            4: {
                'title_pt': 'Consultar seu palmares pessoal',
                'steps_pt': [
                    "Acessar Meu palmares : No seu perfil de praticante, clique em 'Palmares'. Seu historico de competicoes e exibido.",
                    "Ver as estatisticas : Consulte: numero de competicoes, medalhas (ouro/prata/bronze), porcentagem de vitorias, progressao ao longo do tempo.",
                    "Compartilhar seu palmares : Gere um link publico para seu palmares ou exporte-o em PDF para seus expedientes de candidatura ou patrocinio.",
                ],
                'tip_pt': 'Seu palmares e atualizado automaticamente apos cada competicao. Ele e visivel no seu perfil publico se voce permitir.',
            },
        },
    },

    # =========================================================================
    # Secao 8: Gestao de Graduacoes (5 tutoriais)
    # =========================================================================
    8: {
        'title_pt': 'Gestao de Graduacoes',
        'tutorials': {
            1: {
                'title_pt': 'Configurar o sistema de graduacoes',
                'steps_pt': [
                    "Acessar a configuracao : Em Configuracoes > Graduacoes, selecione a disciplina e defina seu sistema de graduacoes.",
                    "Criar os niveis : Adicione os niveis em ordem: Faixa branca, Amarela, Laranja, Verde, Azul, Marrom, Preta 1o Dan, 2o Dan, etc.",
                    "Definir os pre-requisitos : Para cada graduacao, defina: tempo minimo na graduacao anterior, idade minima, numero minimo de aulas, se e necessario exame.",
                    "Atribuir as cores : Atribua as cores das faixas para a exibicao na interface e nos perfis.",
                ],
                'tip_pt': 'Os sistemas de graduacao padrao (Judo, Karate, TKD, BJJ) estao pre-configurados. Voce pode personaliza-los ou criar novos.',
            },
            2: {
                'title_pt': 'Atribuir uma graduacao a um praticante',
                'steps_pt': [
                    "Acessar a ficha : Na ficha do praticante, clique na aba Graduacoes e depois em 'Atribuir uma nova graduacao'.",
                    "Selecionar a graduacao : Escolha a graduacao da lista. O sistema verifica automaticamente os pre-requisitos (tempo, idade, exames).",
                    "Inserir os detalhes : Adicione a data de atribuicao, o local, a banca examinadora e as observacoes.",
                    "Atribuicao em massa : Em Graduacoes > Atribuicao em massa, selecione varios praticantes e atribua a mesma graduacao a todos.",
                ],
                'tip_pt': 'Um e-mail de parabens e enviado automaticamente ao praticante com sua nova graduacao.',
            },
            3: {
                'title_pt': 'Organizar um exame de graduacao',
                'steps_pt': [
                    "Criar o exame : Em Graduacoes > Exames, crie um novo exame: data, local, disciplina, graduacoes abrangidas, banca examinadora.",
                    "Inscrever candidatos : Adicione os candidatos manualmente ou permita a auto-inscricao. O sistema verifica os pre-requisitos de cada um.",
                    "No dia do exame : Use a interface de exame para avaliar cada candidato: tecnicas exigidas, combate, teoria.",
                    "Publicar os resultados : Valide os aprovados e reprovados. As graduacoes sao atribuidas automaticamente aos candidatos aprovados.",
                ],
                'tip_pt': 'Os exames de graduacao podem ser vinculados a uma competicao (ex.: promocao de graduacao durante um torneio).',
            },
            4: {
                'title_pt': 'Gerenciar o historico e a progressao de graduacoes',
                'steps_pt': [
                    "Ver o historico : A ficha de cada praticante exibe o historico completo de graduacoes: data, local, banca examinadora, observacoes.",
                    "Visualizar a progressao : Um grafico mostra a progressao ao longo do tempo. Compare com a media do clube.",
                    "Revogar uma graduacao : Em caso de erro, revogue uma graduacao com um motivo. O historico mantem o registro da revogacao.",
                ],
                'tip_pt': 'O historico de graduacoes e transferivel se o praticante mudar de clube.',
            },
            5: {
                'title_pt': 'Gerar certificados de graduacao',
                'steps_pt': [
                    "Acessar os certificados : Em Graduacoes > Certificados, selecione o praticante e a graduacao para a qual gerar um certificado.",
                    "Escolher o modelo : Selecione um modelo de certificado: oficial (com logotipo da federacao), do clube ou personalizado.",
                    "Personalizar : Adicione as assinaturas, o selo do clube e as mencoes especiais. O codigo QR de verificacao e adicionado automaticamente.",
                    "Gerar e distribuir : Gere o PDF. Imprima ou envie por e-mail. O codigo QR permite que qualquer pessoa verifique a autenticidade do certificado.",
                ],
                'tip_pt': 'O codigo QR de verificacao direciona para uma pagina publica do MartialComp que confirma a validade da graduacao.',
            },
        },
    },

    # =========================================================================
    # Secao 9: Gestao da Federacao (8 tutoriais)
    # =========================================================================
    9: {
        'title_pt': 'Gestao da Federacao',
        'tutorials': {
            1: {
                'title_pt': 'Gerenciar os clubes filiados',
                'steps_pt': [
                    "Visao geral : O painel da federacao exibe o mapa dos clubes filiados, seu status (ativo, pendente, vencido) e estatisticas.",
                    "Processar as solicitacoes : As novas solicitacoes de filiacao aparecem em Clubes > Pendentes. Analise os documentos e aprove ou recuse.",
                    "Monitorar as renovacoes : Visualize as filiacoes proximas do vencimento. Envie lembretes automaticos 30, 15 e 7 dias antes.",
                ],
                'tip_pt': 'O painel da federacao fornece uma visao em tempo real do numero total de praticantes licenciados em todos os clubes.',
            },
            2: {
                'title_pt': 'Gerenciar temporadas e contribuicoes',
                'steps_pt': [
                    "Criar uma temporada : Em Temporadas > Nova, defina as datas de inicio e fim e as tarifas de contribuicoes por tipo (clube, individual, juvenil, senior).",
                    "Configurar as contribuicoes : Defina os valores por categoria: filiacao do clube (fixo), licenca individual (por praticante), seguro (opcional).",
                    "Monitorar os pagamentos : Visualize as contribuicoes recebidas, pendentes e vencidas em tempo real. Envie lembretes automaticos.",
                    "Encerrar a temporada : Ao final da temporada, encerre-a para gerar o relatorio financeiro e preparar a proxima temporada.",
                ],
                'tip_pt': 'As contribuicoes podem ser pagas online via Stripe ou por transferencia bancaria. O acompanhamento e automatico em ambos os casos.',
            },
            3: {
                'title_pt': 'Supervisionar as competicoes',
                'steps_pt': [
                    "Visao global : O calendario da federacao exibe todas as competicoes dos clubes filiados, com status e numero de participantes.",
                    "Homologar uma competicao : Os clubes enviam suas competicoes para homologacao. Verifique as regras, os juizes e valide.",
                    "Ver os resultados : Acesse os resultados de todas as competicoes homologadas. As classificacoes nacionais sao atualizadas automaticamente.",
                ],
                'tip_pt': 'As competicoes homologadas pela federacao sao destacadas no diretorio e no calendario publico.',
            },
            4: {
                'title_pt': 'Gerenciar os juizes e suas qualificacoes',
                'steps_pt': [
                    "Banco de dados de juizes : Visualize o banco de dados de juizes filiados com suas qualificacoes, especialidades e historico de atividade.",
                    "Gerenciar os niveis : Atribua niveis de qualificacao: regional, nacional, internacional. Defina os criterios de promocao.",
                    "Acompanhamento de neutralidade : O MartialComp analisa as estatisticas de pontuacao de cada juiz e detecta possiveis vieses.",
                ],
                'tip_pt': 'Os juizes com um historico de pontuacao equilibrado sao destacados para as competicoes importantes.',
            },
            5: {
                'title_pt': 'Gerenciar as certificacoes',
                'steps_pt': [
                    "Criar um modelo : Projete seus modelos de certificado com o logotipo da federacao, as mencoes legais e os campos dinamicos.",
                    "Emitir certificados : Gere certificados para: graduacoes, qualificacoes de juizes, diplomas de ensino, diversas atestacoes.",
                    "Verificacao publica : Cada certificado possui um codigo QR unico. Qualquer pessoa pode escanea-lo para verificar a autenticidade em martialcomp.com.",
                ],
                'tip_pt': 'Os certificados digitais sao a prova de falsificacao gracas ao codigo QR de verificacao vinculado ao MartialComp.',
            },
            6: {
                'title_pt': 'Personalizar o site publico da federacao',
                'steps_pt': [
                    "Acessar o construtor do site : Em Configuracoes > Site publico, abra o editor de pagina. Sua federacao tem uma URL: federacao.martialcomp.com.",
                    "Personalizar a aparencia : Escolha cores, tema, banner e logotipo. Adicione uma descricao e os links para suas redes sociais.",
                    "Adicionar conteudo : Publique noticias, galerias de fotos, videos, calendario de competicoes e documentos para download.",
                    "Gerenciar as paginas : Crie paginas adicionais: Historia, Diretoria, Regulamento, Contato.",
                ],
                'tip_pt': 'O site publico e otimizado para SEO. Quanto mais completo estiver, melhor se posicionara no Google.',
            },
            7: {
                'title_pt': 'Ver estatisticas e relatorios',
                'steps_pt': [
                    "Painel analitico : O painel exibe os KPIs: numero de clubes, praticantes, competicoes, licencas ativas, crescimento.",
                    "Relatorios por clube : Gere relatorios detalhados por clube: numero de membros, contribuicoes, participacao em competicoes, graduacoes atribuidas.",
                    "Relatorios por disciplina : Analise a distribuicao por disciplina, idade, sexo. Identifique as tendencias de crescimento.",
                    "Exportar e compartilhar : Exporte os relatorios em PDF, Excel ou CSV para suas assembleias gerais e relatorios oficiais.",
                ],
                'tip_pt': 'Os relatorios sao atualizados em tempo real. Programe envios automaticos mensais ou trimestrais.',
            },
            8: {
                'title_pt': 'Gerenciar os programas de formacao',
                'steps_pt': [
                    "Criar um programa : Em Formacao > Novo, defina o programa: titulo, disciplina, nivel, duracao, pre-requisitos.",
                    "Planejar as sessoes : Adicione as sessoes de formacao: datas, locais, formadores, numero de vagas.",
                    "Gerenciar as inscricoes : Treinadores e juizes se inscrevem online. Valide as inscricoes e envie as convocacoes.",
                    "Acompanhamento e certificacao : Monitore a frequencia nas sessoes. Emita as certificacoes para os participantes que completaram o programa.",
                ],
                'tip_pt': 'Os programas de formacao concluidos aparecem automaticamente nos perfis de treinadores e juizes.',
            },
        },
    },

    # =========================================================================
    # Secao 10: Financas (5 tutoriais)
    # =========================================================================
    10: {
        'title_pt': 'Financas',
        'tutorials': {
            1: {
                'title_pt': 'Monitorar as transacoes do clube',
                'steps_pt': [
                    "Visao geral : O painel financeiro exibe: saldo, receitas do mes, despesas e grafico de tendencias.",
                    "Registrar uma transacao : Adicione uma receita ou despesa: valor, data, categoria (mensalidades, equipamentos, aluguel), descricao.",
                    "Categorizacao automatica : O MartialComp categoriza automaticamente as transacoes recorrentes. Personalize as categorias conforme suas necessidades.",
                ],
                'tip_pt': 'Conecte sua conta bancaria para importar automaticamente as transacoes e simplificar a conciliacao.',
            },
            2: {
                'title_pt': 'Criar e enviar faturas',
                'steps_pt': [
                    "Criar uma fatura : Em Financas > Faturas > Nova, selecione o destinatario (praticante, clube, patrocinador) e as linhas de faturamento.",
                    "Personalizar : Adicione seu logotipo, as notas legais, os termos de pagamento. Escolha a moeda e a aliquota de impostos.",
                    "Enviar : Envie a fatura por e-mail. O destinatario recebe um link de pagamento online (Stripe) e a fatura em PDF.",
                    "Monitorar os pagamentos : Visualize as faturas pagas, pendentes e vencidas. Envie lembretes automaticos.",
                ],
                'tip_pt': 'As mensalidades dos praticantes geram automaticamente faturas se voce ativar essa opcao.',
            },
            3: {
                'title_pt': 'Gerenciar os pagamentos online (Stripe)',
                'steps_pt': [
                    "Conectar o Stripe : Em Configuracoes > Pagamentos, clique em 'Conectar Stripe'. Siga os passos para vincular sua conta Stripe.",
                    "Configurar o checkout : Defina as tarifas para: mensalidades, inscricoes em competicoes, loja. Ative os pagamentos recorrentes se necessario.",
                    "Testar o pagamento : Use o modo de teste do Stripe para verificar que tudo funciona antes de ativar os pagamentos reais.",
                    "Monitorar as receitas : O painel do Stripe no MartialComp exibe os pagamentos recebidos, reembolsos e transferencias para sua conta bancaria.",
                ],
                'tip_pt': 'O Stripe cobra uma comissao de 1,4% + 0,25 EUR por transacao na Europa. Os fundos sao transferidos em 2-7 dias.',
            },
            4: {
                'title_pt': 'Importar extratos bancarios',
                'steps_pt': [
                    "Baixar o extrato : No seu banco, exporte o extrato em formato CSV, OFX ou QIF.",
                    "Importar no MartialComp : Em Financas > Importar, carregue o arquivo. O MartialComp detecta o formato e mapeia as colunas.",
                    "Conciliar : O sistema emparelha automaticamente as transacoes importadas com as faturas e mensalidades existentes.",
                    "Validar : Verifique os emparelhamentos, corrija erros e valide. As transacoes sem correspondencia sao adicionadas como pendentes.",
                ],
                'tip_pt': 'As importacoes bancarias mensais mantem sua contabilidade em dia sem entrada manual.',
            },
            5: {
                'title_pt': 'Gerenciar as mensalidades dos praticantes',
                'steps_pt': [
                    "Configurar as tarifas : Em Financas > Mensalidades, defina as tarifas anuais por categoria: crianca, adolescente, adulto, familia.",
                    "Emitir as solicitacoes de pagamento : No inicio da temporada, gere as solicitacoes de pagamento para todos os membros. Cada um recebe um e-mail com um link de pagamento.",
                    "Monitorar os pagamentos : Visualize as mensalidades pagas, pendentes e vencidas. O status aparece na ficha de cada praticante.",
                    "Enviar lembretes : Programe lembretes automaticos: 1 semana, 2 semanas, 1 mes apos a data de vencimento.",
                ],
                'tip_pt': 'Os praticantes com mensalidades vencidas podem ser impedidos de se inscrever em competicoes.',
            },
        },
    },

    # =========================================================================
    # Secao 11: Eventos e Calendario (3 tutoriais)
    # =========================================================================
    11: {
        'title_pt': 'Eventos e Calendario',
        'tutorials': {
            1: {
                'title_pt': 'Criar um evento (seminario, gala, assembleia)',
                'steps_pt': [
                    "Criar o evento : Em Calendario > Novo evento, insira: tipo (seminario, gala, assembleia, portas abertas), titulo, datas, local e descricao.",
                    "Configurar as inscricoes : Ative as inscricoes online. Defina o numero de vagas, a tarifa (gratuita ou paga) e a data limite de inscricao.",
                    "Publicar : Publique o evento. Ele aparece no calendario do clube e pode ser compartilhado nas redes sociais.",
                ],
                'tip_pt': 'Os seminarios com mestres convidados sao excelentes ferramentas de marketing. Adicione sua foto e biografia para atrair mais pessoas.',
            },
            2: {
                'title_pt': 'Gerenciar os eventos recorrentes',
                'steps_pt': [
                    "Criar a recorrencia : Durante a criacao, marque 'Evento recorrente'. Defina a frequencia: diaria, semanal, mensal.",
                    "Gerenciar excecoes : Cancele ou modifique uma ocorrencia individual sem afetar as demais (ex.: aula cancelada por feriado).",
                    "Modificar a serie : Modifique toda a serie (ex.: mudanca permanente de horario) ou uma unica ocorrencia.",
                ],
                'tip_pt': 'As aulas semanais devem ser criadas como eventos recorrentes para aparecer automaticamente no calendario.',
            },
            3: {
                'title_pt': 'Acompanhar inscricoes e frequencia',
                'steps_pt': [
                    "Ver os inscritos : No evento, visualize a lista de inscritos com seu status: inscrito, confirmado, cancelado.",
                    "Registrar a frequencia : No dia do evento, registre a frequencia por lista ou codigo QR.",
                    "Exportar : Exporte a lista de participantes em CSV ou PDF para seus arquivos.",
                ],
                'tip_pt': 'A taxa de participacao em eventos e um indicador-chave do engajamento dos seus membros.',
            },
        },
    },

    # =========================================================================
    # Secao 12: Gestao Familiar (3 tutoriais)
    # =========================================================================
    12: {
        'title_pt': 'Gestao Familiar',
        'tutorials': {
            1: {
                'title_pt': 'Criar um grupo familiar',
                'steps_pt': [
                    "Acessar os grupos familiares : No seu perfil, va em Configuracoes > Grupo Familiar > Criar.",
                    "Adicionar membros : Adicione cada membro da familia: conjuge, filhos. Vincule suas contas MartialComp existentes ou crie novas.",
                    "Definir o responsavel : O responsavel do grupo familiar recebe todas as notificacoes e gerencia os pagamentos de toda a familia.",
                ],
                'tip_pt': 'Alguns clubes oferecem tarifas familiares (desconto a partir do 3o membro). O grupo familiar ativa automaticamente esses descontos.',
            },
            2: {
                'title_pt': 'Inscrever toda a familia em uma competicao',
                'steps_pt': [
                    "Inscricao em grupo : Na competicao, clique em 'Inscrever minha familia'. Os membros elegiveis do seu grupo familiar sao exibidos.",
                    "Selecionar e confirmar : Selecione os membros a inscrever. As categorias sao sugeridas automaticamente para cada um.",
                    "Pagamento unico : Pague todas as inscricoes em uma unica transacao.",
                ],
                'tip_pt': 'A inscricao em grupo economiza tempo precioso quando varios filhos participam da mesma competicao.',
            },
            3: {
                'title_pt': 'Central de pagamentos familiar',
                'steps_pt': [
                    "Visao geral : A central familiar exibe todas as mensalidades, inscricoes e faturas da familia em uma unica tela.",
                    "Pagamento agrupado : Agrupe varios pagamentos pendentes e pague em uma unica transacao.",
                    "Historico : Visualize o historico completo de pagamentos da familia com recibos para download.",
                ],
                'tip_pt': 'Ative o debito automatico para nunca esquecer uma mensalidade.',
            },
        },
    },

    # =========================================================================
    # Secao 13: Gestao de Tarefas (Kanban) (2 tutoriais)
    # =========================================================================
    13: {
        'title_pt': 'Gestao de Tarefas (Kanban)',
        'tutorials': {
            1: {
                'title_pt': 'Usar o quadro Kanban',
                'steps_pt': [
                    "Criar um quadro : Em Ferramentas > Kanban, crie um novo quadro: nome, descricao e membros convidados.",
                    "Adicionar colunas : Crie as colunas do seu fluxo de trabalho: A fazer, Em andamento, Em espera, Concluido. Personalize nomes e cores.",
                    "Criar tarefas : Adicione tarefas com: titulo, descricao, data limite, responsavel, prioridade (alta/media/baixa) e etiquetas.",
                    "Gerenciar arrastando e soltando : Mova as tarefas entre colunas arrastando-as. O historico de movimentacoes e preservado.",
                ],
                'tip_pt': 'Crie um quadro dedicado para cada competicao a organizar. As tarefas padrao (reservar o local, encomendar medalhas, etc.) podem ser importadas de um modelo.',
            },
            2: {
                'title_pt': 'Gerenciar as tarefas organizacionais',
                'steps_pt': [
                    "Modelo de competicao : Use o modelo 'Organizacao de Competicao' que contem tarefas padrao: logistica, comunicacao, juizes, medalhas, etc.",
                    "Atribuir aos membros : Atribua cada tarefa a um membro da equipe organizadora. Defina os prazos.",
                    "Acompanhar o progresso : O percentual de avanco geral e exibido no topo do quadro. As tarefas vencidas sao destacadas em vermelho.",
                ],
                'tip_pt': 'O quadro Kanban e acessivel pelo aplicativo movel para atualizar as tarefas em qualquer lugar.',
            },
        },
    },

    # =========================================================================
    # Secao 14: Loja Online (2 tutoriais)
    # =========================================================================
    14: {
        'title_pt': 'Loja Online',
        'tutorials': {
            1: {
                'title_pt': 'Configurar a loja do clube',
                'steps_pt': [
                    "Ativar a loja : Em Configuracoes > Loja, ative a funcionalidade de comercio eletronico. Conecte sua conta Stripe se ainda nao o fez.",
                    "Adicionar produtos : Crie seus produtos: nome, descricao, fotos, preco, tamanhos/variantes disponiveis, estoque.",
                    "Organizar por categorias : Classifique seus produtos: Uniformes (kimono, dobok, luvas), Equipamentos (protecoes, bolsas), Acessorios (faixas, emblemas), Merchandising.",
                    "Publicar a loja : Sua loja e acessivel a partir da pagina publica do seu clube. Compartilhe o link ou codigo QR.",
                ],
                'tip_pt': 'Ofereca kits (kimono + faixa + bolsa) com desconto para aumentar o ticket medio.',
            },
            2: {
                'title_pt': 'Realizar um pedido',
                'steps_pt': [
                    "Navegar pela loja : Na pagina do seu clube, acesse a loja. Navegue pelos produtos por categoria.",
                    "Adicionar ao carrinho : Selecione o tamanho/variante e adicione ao carrinho. O carrinho e mantido entre sessoes.",
                    "Fazer o pedido e pagar : Confirme seu carrinho, escolha o metodo de entrega (retirada no dojo ou envio postal) e pague online.",
                    "Acompanhar o pedido : Receba notificacoes a cada etapa: pedido confirmado, em preparacao, pronto para retirada / enviado.",
                ],
                'tip_pt': 'O modo \'Retirada no Dojo\' evita custos de envio. O treinador entregara seu pedido na proxima aula.',
            },
        },
    },

    # =========================================================================
    # Secao 15: Funcionalidades Avancadas (5 tutoriais)
    # =========================================================================
    15: {
        'title_pt': 'Funcionalidades Avancadas',
        'tutorials': {
            1: {
                'title_pt': 'Configurar a transmissao de competicoes',
                'steps_pt': [
                    "Preparar a transmissao : Crie um evento ao vivo no YouTube, Twitch ou Facebook. Copie a URL da transmissao e a chave de transmissao.",
                    "Configurar no MartialComp : Na competicao, va em Configuracoes > Transmissao. Cole a URL e ative a exibicao na pagina publica.",
                    "Overlay de pontuacao : Ative o overlay do MartialComp que exibe a pontuacao ao vivo na transmissao de video. Personalize a posicao e o estilo.",
                    "Iniciar e testar : Inicie a transmissao e verifique se o overlay funciona. Os espectadores verao a pontuacao ao vivo na transmissao.",
                ],
                'tip_pt': 'A transmissao com overlay de pontuacao do MartialComp da um aspecto profissional mesmo a competicoes pequenas.',
            },
            2: {
                'title_pt': 'Usar o aplicativo movel',
                'steps_pt': [
                    "Baixar o app : Busque 'MartialComp' na Play Store (Android) ou App Store (iOS). Instale e abra.",
                    "Fazer login : Faca login com sua conta MartialComp existente. Voce tambem pode usar o acesso com Google, Facebook ou Apple.",
                    "Descobrir a interface movel : O app oferece: perfil, resultados, calendario, notificacoes push, codigo QR pessoal e inscricao em competicoes.",
                    "Modo offline : Os dados essenciais (perfil, graduacao, licenca) estao disponiveis sem conexao. Sincronizacao automatica ao reconectar.",
                ],
                'tip_pt': 'Ative as notificacoes push para receber alertas de resultados ao vivo durante as competicoes.',
            },
            3: {
                'title_pt': 'Alternar papel no aplicativo',
                'steps_pt': [
                    "Acessar o seletor de papel : Toque no seu avatar na parte superior da tela ou deslize da esquerda para abrir o menu lateral.",
                    "Selecionar um papel : Sua lista de papeis aparece: Treinador, Praticante, Juiz, Responsavel de Clube. Toque no papel desejado.",
                    "Interface adaptada : O painel de controle e o menu sao atualizados imediatamente para refletir o papel selecionado.",
                ],
                'tip_pt': 'Voce pode ser treinador em um clube e praticante em outro. Cada papel esta vinculado a sua organizacao.',
            },
            4: {
                'title_pt': 'Importacao/Exportacao avancada de dados',
                'steps_pt': [
                    "Formatos suportados : O MartialComp suporta importacao e exportacao em CSV, Excel (XLSX), JSON e PDF. Cada modulo tem suas proprias opcoes.",
                    "Importacao com mapeamento : A interface de mapeamento permite associar qualquer estrutura de arquivo com os campos do MartialComp.",
                    "Exportacao personalizada : Selecione os campos a exportar, os filtros e o formato. Programe exportacoes automaticas recorrentes.",
                    "Operacoes em massa : As operacoes em massa permitem a modificacao em lote de: graduacao, grupo, status de inscricao, etc.",
                ],
                'tip_pt': 'A exportacao JSON e ideal para integracoes com sistemas de terceiros (site, aplicativo externo, CRM).',
            },
            5: {
                'title_pt': 'Gerenciar juizes ad hoc (voluntarios)',
                'steps_pt': [
                    "Criar um juiz temporario : No dia da competicao, em Juizes > Adicionar voluntario, crie um perfil temporario: nome, clube e especialidade.",
                    "Atribuir um PIN : Um PIN unico e gerado automaticamente. O voluntario usa este PIN para acessar a interface de pontuacao.",
                    "Atribuir as categorias : Atribua o juiz voluntario as categorias como um juiz regular. Ele pode comecar a avaliar imediatamente.",
                    "Apos a competicao : O perfil temporario e arquivado apos a competicao. As pontuacoes sao preservadas no historico.",
                ],
                'tip_pt': 'Os juizes ad hoc sao essenciais para competicoes pequenas onde o numero de juizes oficiais e limitado.',
            },
        },
    },
}


class Command(BaseCommand):
    help = 'Translate all 81 tutorials from French to Portuguese (hardcoded translations)'

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

            section.title_pt = sec_data['title_pt']
            if not dry_run:
                section.save(update_fields=['title_pt'])
            sections_updated += 1
            self.stdout.write(self.style.SUCCESS(
                f'  Section {section.order}: {section.title_fr} -> {sec_data["title_pt"]}'
            ))

            for tutorial in section.tutorials.all().order_by('number'):
                tut_data = sec_data.get('tutorials', {}).get(tutorial.number)
                if not tut_data:
                    self.stdout.write(self.style.WARNING(
                        f'    No translation for tutorial {section.order}.{tutorial.number}: {tutorial.title}'
                    ))
                    tutorials_missing += 1
                    continue

                tutorial.title_pt = tut_data['title_pt']
                tutorial.steps_pt = json.dumps(tut_data['steps_pt'], ensure_ascii=False)
                tutorial.tip_pt = tut_data.get('tip_pt', '')

                if not dry_run:
                    tutorial.save(update_fields=['title_pt', 'steps_pt', 'tip_pt'])

                tutorials_updated += 1
                self.stdout.write(f'    {section.order}.{tutorial.number}: {tut_data["title_pt"]}')

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
