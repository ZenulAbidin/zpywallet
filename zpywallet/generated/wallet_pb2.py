# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: wallet.proto
# Protobuf Python Version: 4.25.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0cwallet.proto\"6\n\x07RPCNode\x12\x0b\n\x03url\x18\x01 \x01(\t\x12\x0c\n\x04user\x18\x02 \x01(\t\x12\x10\n\x08password\x18\x03 \x01(\t\"\xc9\x02\n\x06Wallet\x12\x19\n\x07network\x18\x01 \x01(\x0e\x32\x08.Network\x12\x1d\n\x15\x65ncrypted_seed_phrase\x18\x02 \x01(\x0c\x12\x0e\n\x06height\x18\x03 \x01(\x07\x12\x19\n\x11receive_gap_limit\x18\x04 \x01(\x07\x12\x18\n\x10\x63hange_gap_limit\x18\x05 \x01(\x07\x12\x1b\n\taddresses\x18\x06 \x03(\x0b\x32\x08.Address\x12\"\n\x0ctransactions\x18\x07 \x03(\x0b\x32\x0c.Transaction\x12\x18\n\x10\x63rypto_providers\x18\x08 \x01(\r\x12$\n\x12\x66ullnode_endpoints\x18\t \x03(\x0b\x32\x08.RPCNode\x12#\n\x11\x65splora_endpoints\x18\n \x03(\x0b\x32\x08.RPCNode\x12\x1a\n\x12\x62lockcypher_tokens\x18\x0b \x03(\t\";\n\x07\x41\x64\x64ress\x12\x0f\n\x07\x61\x64\x64ress\x18\x01 \x01(\t\x12\x0e\n\x06pubkey\x18\x02 \x01(\t\x12\x0f\n\x07privkey\x18\x03 \x01(\t\"a\n\x12\x42TCLikeTransaction\x12\x0b\n\x03\x66\x65\x65\x18\x01 \x01(\x04\x12\x1d\n\x06inputs\x18\x02 \x03(\x0b\x32\r.BTCLikeInput\x12\x1f\n\x07outputs\x18\x03 \x03(\x0b\x32\x0e.BTCLikeOutput\"Q\n\x0c\x42TCLikeInput\x12\x0c\n\x04txid\x18\x01 \x01(\t\x12\r\n\x05index\x18\x02 \x01(\r\x12\x0e\n\x06\x61mount\x18\x03 \x01(\x04\x12\x14\n\x0cwitness_data\x18\x04 \x03(\x0c\"N\n\rBTCLikeOutput\x12\x0e\n\x06\x61mount\x18\x01 \x01(\x04\x12\x0f\n\x07\x61\x64\x64ress\x18\x02 \x01(\t\x12\r\n\x05index\x18\x03 \x01(\x04\x12\r\n\x05spent\x18\x04 \x01(\x08\"]\n\x12\x45THLikeTransaction\x12\x0e\n\x06txfrom\x18\x01 \x01(\t\x12\x0c\n\x04txto\x18\x02 \x01(\t\x12\x0e\n\x06\x61mount\x18\x03 \x01(\x04\x12\x0b\n\x03gas\x18\x04 \x01(\x04\x12\x0c\n\x04\x64\x61ta\x18\x05 \x01(\x0c\"\xe8\x01\n\x0bTransaction\x12\x0c\n\x04txid\x18\x01 \x01(\t\x12\x11\n\ttimestamp\x18\x02 \x01(\x04\x12\x11\n\tconfirmed\x18\x03 \x01(\x08\x12\x0e\n\x06height\x18\x04 \x01(\x04\x12\x11\n\ttotal_fee\x18\x05 \x01(\x04\x12\x1e\n\nfee_metric\x18\x06 \x01(\x0e\x32\n.FeeMetric\x12\x30\n\x13\x62tclike_transaction\x18\x0f \x01(\x0b\x32\x13.BTCLikeTransaction\x12\x30\n\x13\x65thlike_transaction\x18\x0e \x01(\x0b\x32\x13.ETHLikeTransaction\"{\n\x04UTXO\x12\x0e\n\x06\x61mount\x18\x01 \x01(\x04\x12\x0f\n\x07\x61\x64\x64ress\x18\x02 \x01(\t\x12\x0c\n\x04txid\x18\x03 \x01(\t\x12\r\n\x05index\x18\x04 \x01(\x04\x12\x12\n\nprivatekey\x18\x05 \x01(\t\x12\x11\n\tconfirmed\x18\x06 \x01(\x08\x12\x0e\n\x06height\x18\x07 \x01(\x04*\x8b\x04\n\x07Network\x12\x1a\n\x16\x42ITCOIN_SEGWIT_MAINNET\x10\x00\x12\x13\n\x0f\x42ITCOIN_MAINNET\x10\x01\x12\x1a\n\x16\x42ITCOIN_SEGWIT_TESTNET\x10\x02\x12\x13\n\x0f\x42ITCOIN_TESTNET\x10\x03\x12\x1b\n\x17LITECOIN_SEGWIT_MAINNET\x10\x04\x12\x14\n\x10LITECOIN_MAINNET\x10\x05\x12\x1f\n\x1bLITECOIN_BTC_SEGWIT_MAINNET\x10\x06\x12\x18\n\x14LITECOIN_BTC_MAINNET\x10\x07\x12\x1b\n\x17LITECOIN_SEGWIT_TESTNET\x10\x08\x12\x14\n\x10LITECOIN_TESTNET\x10\t\x12\x14\n\x10\x45THEREUM_MAINNET\x10\n\x12\x14\n\x10\x44OGECOIN_MAINNET\x10\x0b\x12\x18\n\x14\x44OGECOIN_BTC_MAINNET\x10\x0c\x12\x14\n\x10\x44OGECOIN_TESTNET\x10\r\x12\x10\n\x0c\x44\x41SH_MAINNET\x10\x0e\x12\x19\n\x15\x44\x41SH_INVERTED_MAINNET\x10\x0f\x12\x14\n\x10\x44\x41SH_BTC_MAINNET\x10\x10\x12\x10\n\x0c\x44\x41SH_TESTNET\x10\x11\x12\x19\n\x15\x44\x41SH_INVERTED_TESTNET\x10\x12\x12\x18\n\x14\x42ITCOIN_CASH_MAINNET\x10\x13\x12\x17\n\x13\x42LOCKCYPHER_TESTNET\x10\x14*\"\n\x0b\x42\x43YProvider\x12\x13\n\x0f\x42\x43Y_BLOCKCYPHER\x10\x00*\x9c\x01\n\x0b\x42TCProvider\x12\x13\n\x0f\x42TC_BLOCKCYPHER\x10\x00\x12\x13\n\x0f\x42TC_BLOCKSTREAM\x10\x01\x12\x14\n\x10\x42TC_MEMPOOLSPACE\x10\x02\x12\x11\n\rBTC_BTCDOTCOM\x10\x03\x12\x17\n\x13\x42TC_BLOCKCHAIN_INFO\x10\x04\x12\x0f\n\x0b\x42TC_ESPLORA\x10\x05\x12\x10\n\x0c\x42TC_FULLNODE\x10\x06*\x88\x01\n\x0f\x42TCTestProvider\x12\x17\n\x13\x42TCTEST_BLOCKCYPHER\x10\x00\x12\x17\n\x13\x42TCTEST_BLOCKSTREAM\x10\x01\x12\x18\n\x14\x42TCTEST_MEMPOOLSPACE\x10\x02\x12\x13\n\x0f\x42TCTEST_ESPLORA\x10\x03\x12\x14\n\x10\x42TCTEST_FULLNODE\x10\x04*7\n\x0c\x44\x41SHProvider\x12\x14\n\x10\x44\x41SH_BLOCKCYPHER\x10\x00\x12\x11\n\rDASH_FULLNODE\x10\x01*8\n\x0c\x44OGEProvider\x12\x14\n\x10\x44OGE_BLOCKCYPHER\x10\x00\x12\x12\n\x0e\x44OGE_DOGECHAIN\x10\x01*\x1f\n\x0b\x45THProvider\x12\x10\n\x0c\x45TH_FULLNODE\x10\x00*4\n\x0bLTCProvider\x12\x13\n\x0fLTC_BLOCKCYPHER\x10\x00\x12\x10\n\x0cLTC_FULLNODE\x10\x01*)\n\tFeeMetric\x12\x08\n\x04\x42YTE\x10\x00\x12\t\n\x05VBYTE\x10\x01\x12\x07\n\x03WEI\x10\x02\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'wallet_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_NETWORK']._serialized_start=1183
  _globals['_NETWORK']._serialized_end=1706
  _globals['_BCYPROVIDER']._serialized_start=1708
  _globals['_BCYPROVIDER']._serialized_end=1742
  _globals['_BTCPROVIDER']._serialized_start=1745
  _globals['_BTCPROVIDER']._serialized_end=1901
  _globals['_BTCTESTPROVIDER']._serialized_start=1904
  _globals['_BTCTESTPROVIDER']._serialized_end=2040
  _globals['_DASHPROVIDER']._serialized_start=2042
  _globals['_DASHPROVIDER']._serialized_end=2097
  _globals['_DOGEPROVIDER']._serialized_start=2099
  _globals['_DOGEPROVIDER']._serialized_end=2155
  _globals['_ETHPROVIDER']._serialized_start=2157
  _globals['_ETHPROVIDER']._serialized_end=2188
  _globals['_LTCPROVIDER']._serialized_start=2190
  _globals['_LTCPROVIDER']._serialized_end=2242
  _globals['_FEEMETRIC']._serialized_start=2244
  _globals['_FEEMETRIC']._serialized_end=2285
  _globals['_RPCNODE']._serialized_start=16
  _globals['_RPCNODE']._serialized_end=70
  _globals['_WALLET']._serialized_start=73
  _globals['_WALLET']._serialized_end=402
  _globals['_ADDRESS']._serialized_start=404
  _globals['_ADDRESS']._serialized_end=463
  _globals['_BTCLIKETRANSACTION']._serialized_start=465
  _globals['_BTCLIKETRANSACTION']._serialized_end=562
  _globals['_BTCLIKEINPUT']._serialized_start=564
  _globals['_BTCLIKEINPUT']._serialized_end=645
  _globals['_BTCLIKEOUTPUT']._serialized_start=647
  _globals['_BTCLIKEOUTPUT']._serialized_end=725
  _globals['_ETHLIKETRANSACTION']._serialized_start=727
  _globals['_ETHLIKETRANSACTION']._serialized_end=820
  _globals['_TRANSACTION']._serialized_start=823
  _globals['_TRANSACTION']._serialized_end=1055
  _globals['_UTXO']._serialized_start=1057
  _globals['_UTXO']._serialized_end=1180
# @@protoc_insertion_point(module_scope)
