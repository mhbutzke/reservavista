-- Tabela: Pipes
CREATE TABLE IF NOT EXISTS pipes (
    "Codigo" TEXT PRIMARY KEY,
    "Nome" TEXT,
    "Empresa" TEXT
);

-- Tabela: Agencias
CREATE TABLE IF NOT EXISTS agencias (
    "Codigo" TEXT PRIMARY KEY,
    "Nome" TEXT,
    "Empresa" TEXT,
    "Responsavel" TEXT,
    "Endereco" TEXT,
    "Bairro" TEXT,
    "Cidade" TEXT,
    "Cep" TEXT,
    "Uf" TEXT,
    "Pais" TEXT,
    "Fone" TEXT,
    "E-mail" TEXT,
    "Numero" TEXT,
    "Complemento" TEXT,
    "CodigoEmpresa" TEXT,
    "Ddd" TEXT,
    "Cnpj" TEXT,
    "Cpf" TEXT,
    "RazaoSocial" TEXT,
    "Fone2" TEXT,
    "Celular" TEXT,
    "Creci" TEXT,
    "Site" TEXT
);

-- Tabela: Corretores
CREATE TABLE IF NOT EXISTS corretores (
    "Codigo" TEXT PRIMARY KEY,
    "Nome" TEXT
);

-- Tabela: Usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    "Codigo" TEXT PRIMARY KEY,
    "Nome" TEXT,
    "Email" TEXT,
    "Datacadastro" TEXT,
    "RGInscricao" TEXT,
    "RGEmissor" TEXT,
    "CPFCGC" TEXT,
    "Nascimento" TEXT,
    "Nacionalidade" TEXT,
    "CNH" TEXT,
    "CNHExpedicao" TEXT,
    "CNHVencimento" TEXT,
    "Celular" TEXT,
    "Endereco" TEXT,
    "Bairro" TEXT,
    "Cidade" TEXT,
    "UF" TEXT,
    "CEP" TEXT,
    "Pais" TEXT,
    "Fone" TEXT,
    "Fax" TEXT,
    "E-mail" TEXT,
    "Observacoes" TEXT,
    "Administrativo" TEXT,
    "Agenciador" TEXT,
    "Gerente" TEXT,
    "Empresa" TEXT,
    "Celular1" TEXT,
    "Celular2" TEXT,
    "Corretor" TEXT,
    "Datasaida" TEXT,
    "Grupoacesso" TEXT,
    "Nomecompleto" TEXT,
    "Ramal" TEXT,
    "Sexo" TEXT,
    "Exibirnosite" TEXT,
    "RecebeClientesemTrocaautomática" TEXT,
    "Inativo" TEXT,
    "CRECI" TEXT,
    "Estadocivil" TEXT,
    "Diretor" TEXT,
    "MetadeCaptacoes" TEXT,
    "MetaValordeVendas" TEXT,
    "EnderecoTipo" TEXT,
    "EnderecoNumero" TEXT,
    "EnderecoComplemento" TEXT,
    "Bloco" TEXT,
    "Chat" TEXT,
    "CategoriaRanking" TEXT,
    "Atuaçãoemvenda" TEXT,
    "Atuaçãoemlocação" TEXT,
    "DataUltimoLogin" TEXT,
    "CodigoAgencia" TEXT REFERENCES agencias("Codigo"), -- FK
    "Foto" TEXT
);

-- Tabela: Proprietarios
CREATE TABLE IF NOT EXISTS proprietarios (
    "Codigo" TEXT PRIMARY KEY,
    "Nome" TEXT,
    "FotoCliente" TEXT,
    "Foto" TEXT,
    "CodigoAgencia" TEXT REFERENCES agencias("Codigo"), -- FK
    "Corretor" TEXT,
    "Agencia" TEXT,
    "CPFCNPJ" TEXT,
    "CreditoSituacao" TEXT,
    "CreditoMensagem" TEXT,
    "CODIGO_CREDPAGO" TEXT,
    "PossuiAnexo" TEXT,
    "AnexoCodigoFinalidade" TEXT
);

-- Tabela: Clientes
CREATE TABLE IF NOT EXISTS clientes (
    "Codigo" TEXT PRIMARY KEY,
    "Nome" TEXT,
    "CPFCNPJ" TEXT,
    "RG" TEXT,
    "DataNascimento" TEXT,
    "Sexo" TEXT,
    "EstadoCivil" TEXT,
    "Profissao" TEXT,
    "Nacionalidade" TEXT,
    "EmailResidencial" TEXT,
    "FonePrincipal" TEXT,
    "Celular" TEXT,
    "FoneComercial" TEXT,
    "EmailComercial" TEXT,
    "EnderecoResidencial" TEXT,
    "EnderecoNumero" TEXT,
    "EnderecoComplemento" TEXT,
    "BairroResidencial" TEXT,
    "CidadeResidencial" TEXT,
    "UFResidencial" TEXT,
    "CEPResidencial" TEXT,
    "Status" TEXT,
    "DataCadastro" TEXT,
    "DataAtualizacao" TEXT,
    "Observacoes" TEXT
);

-- Tabela: Imóveis (NOVA)
CREATE TABLE IF NOT EXISTS imoveis (
    "Codigo" TEXT PRIMARY KEY,
    "Categoria" TEXT,
    "Bairro" TEXT,
    "Cidade" TEXT,
    "ValorVenda" NUMERIC,
    "ValorLocacao" NUMERIC,
    "AreaTotal" NUMERIC,
    "AreaPrivativa" NUMERIC,
    "Dormitorios" INTEGER,
    "Suites" INTEGER,
    "Vagas" INTEGER,
    "BanheiroSocial" TEXT,
    "Endereco" TEXT,
    "Numero" TEXT,
    "Complemento" TEXT,
    "CEP" TEXT,
    "UF" TEXT,
    "DataCadastro" TIMESTAMP,
    "DataAtualizacao" TIMESTAMP,
    "Status" TEXT,
    "Situacao" TEXT,
    "DescricaoWeb" TEXT,
    "TituloSite" TEXT,
    "CodigoAgencia" TEXT REFERENCES agencias("Codigo") -- FK Opcional
);

-- Tabela: Negocios
CREATE TABLE IF NOT EXISTS negocios (
    "Codigo" TEXT PRIMARY KEY,
    "Titulo" TEXT,
    "ValorVenda" NUMERIC,
    "ValorLocacao" NUMERIC,
    "Fase" TEXT,
    "DataCadastro" TIMESTAMP,
    "DataAtualizacao" TIMESTAMP,
    "DataFechamento" TIMESTAMP,
    "Status" TEXT,
    "CodigoCliente" TEXT REFERENCES clientes("Codigo"), -- FK
    "CodigoCorretor" TEXT REFERENCES corretores("Codigo"), -- FK
    "CodigoAgencia" TEXT REFERENCES agencias("Codigo"), -- FK
    "Origem" TEXT,
    "Midia" TEXT,
    "Observacao" TEXT,
    "ObservacaoPerda" TEXT,
    "NomeCliente" TEXT,
    "NomeCorretor" TEXT,
    "NomeAgencia" TEXT,
    "MotivoPerda" TEXT,
    "DataPerda" TIMESTAMP,
    "DataGanho" TIMESTAMP,
    "PipeID" TEXT REFERENCES pipes("Codigo"), -- FK
    "PipeNome" TEXT,
    "CodigoImovel" TEXT REFERENCES imoveis("Codigo"), -- FK
    "StatusAtividades" TEXT,
    "FotoCliente" TEXT
);

-- Tabela: Atividades
CREATE TABLE IF NOT EXISTS atividades (
    "CodigoAtividade" TEXT,
    "CodigoNegocio" TEXT REFERENCES negocios("Codigo"), -- FK
    PRIMARY KEY ("CodigoNegocio", "CodigoAtividade"),
    "CodigoImovel" TEXT,
    "ValorProposta" NUMERIC,
    "EstadoProposta" TEXT,
    "TextoProposta" TEXT,
    "Aceitacao" TEXT,
    "Automatico" TEXT,
    "Numero" TEXT,
    "Texto" TEXT,
    "Pendente" TEXT,
    "Assunto" TEXT,
    "EtapaAcaoId" TEXT,
    "EtapaAcao" TEXT,
    "TipoAtividade" TEXT,
    "TipoAtividadeId" TEXT,
    "MotivoLost" TEXT,
    "CodigoEmImovel" TEXT,
    "Hora" TEXT,
    "AtividadeCreatedAt" TIMESTAMP,
    "AtividadeUpdatedAt" TIMESTAMP,
    "Data" TIMESTAMP,
    "CodigoCliente" TEXT REFERENCES clientes("Codigo"), -- FK
    "CodigoCorretor" TEXT REFERENCES corretores("Codigo"), -- FK
    "NumeroAgenda" TEXT,
    "DataHora" TIMESTAMP,
    "DataAtualizacao" TIMESTAMP,
    "Local" TEXT,
    "Inicio" TEXT,
    "Final" TEXT,
    "Prioridade" TEXT,
    "Privado" TEXT,
    "AlertaMinutos" TEXT,
    "Excluido" TEXT,
    "Concluido" TEXT,
    "Tarefa" TEXT,
    "DataConclusao" TIMESTAMP,
    "DiaInteiro" TEXT,
    "TipoAgenda" TEXT,
    "CodigoDev" TEXT,
    "IdGoogleCalendar" TEXT,
    "StatusVisita" TEXT,
    "CodigoImobiliaria" TEXT,
    "Icone" TEXT,
    "Duracao" TEXT,
    "FotoCorretor" TEXT,
    "Status" TEXT
);

-- Tabela de Controle de Sincronização
CREATE TABLE IF NOT EXISTS sync_state (
    "entity" TEXT PRIMARY KEY,
    "last_run" TIMESTAMP,
    "updated_at" TIMESTAMP
);

-- Índices para Performance
CREATE INDEX IF NOT EXISTS idx_negocios_data_atualizacao ON negocios("DataAtualizacao");
CREATE INDEX IF NOT EXISTS idx_negocios_cliente ON negocios("CodigoCliente");
CREATE INDEX IF NOT EXISTS idx_negocios_pipe ON negocios("PipeID");
CREATE INDEX IF NOT EXISTS idx_negocios_status ON negocios("Status");

CREATE INDEX IF NOT EXISTS idx_atividades_negocio ON atividades("CodigoNegocio");
CREATE INDEX IF NOT EXISTS idx_atividades_data ON atividades("Data");
CREATE INDEX IF NOT EXISTS idx_atividades_tipo ON atividades("TipoAtividade");

CREATE INDEX IF NOT EXISTS idx_clientes_email ON clientes("EmailResidencial");
CREATE INDEX IF NOT EXISTS idx_clientes_cpf ON clientes("CPFCNPJ");

CREATE INDEX IF NOT EXISTS idx_imoveis_bairro ON imoveis("Bairro");
CREATE INDEX IF NOT EXISTS idx_imoveis_cidade ON imoveis("Cidade");
CREATE INDEX IF NOT EXISTS idx_imoveis_status ON imoveis("Status");
