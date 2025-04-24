MER do projeto 

Entidades (atributos)

produtor_rural (id_produtor, nome_produtor, cpf_produtor, contato_produtor)
terra_plantio (id_terra, id_produtor, localizacao_terra)
cultura (id_cultura, id_produtor, id_terra, localizacao)
sensor (id_sensor, tipo_sensor)
leitura_sensor (id_leitura, id_cultura, id_sensor, valor_leitura, data_leitura)
insumos (id_insumo, tipo_insumo)
aplicacao_insumos (id_aplicacao, id_cultura, data_aplicacao, quantidade_aplicacao)
estacao_do_ano (id_estacao, nome_estacao)

Relacionamentos (interação)

produtor_rural 1:N terra_plantio (Um produtor pode ter uma ou várias terras)
produtor_rural 1:N cultura (Um produtor pode ter uma ou várias culturas)
terra_plantio 1:N cultura (Uma terra de plantio pode ter uma ou várias culturas)
sensor 1:N leitura_sensor (Um sensor pode fazer uma ou várias leituras)
leitura_sensor N:1 cultura (Pode haver uma ou várias leituras de um sensor em uma cultura)
aplicacao_insumos 0:1 cultura (Pode ser feita nenhuma ou várias aplicações de insumos em uma cultura)
insumos M:N aplicacao_insumos (Pode ser feita várias aplicações de vários insumos)

