# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: chats/v2/chat_info_service.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import kik_unofficial.protobuf.protobuf_validation_pb2 as protobuf__validation__pb2
from kik_unofficial.protobuf.common.v2 import model_pb2 as common_dot_v2_dot_model__pb2
from kik_unofficial.protobuf.messaging.v2 import model_pb2 as messaging_dot_v2_dot_model__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='chats/v2/chat_info_service.proto',
  package='mobile.chats.v2',
  syntax='proto3',
  serialized_pb=_b('\n chats/v2/chat_info_service.proto\x12\x0fmobile.chats.v2\x1a\x19protobuf_validation.proto\x1a\x15\x63ommon/v2/model.proto\x1a\x18messaging/v2/model.proto\"M\n\x18GetChatInfoStreamRequest\x12\x31\n\x08\x63hat_ids\x18\x01 \x03(\x0b\x32\x11.common.v2.ChatIdB\x0c\xca\x9d%\x08\x08\x01x\x01\x80\x01\x80\x08\"\x9d\x03\n\x19GetChatInfoStreamResponse\x12\x41\n\x06result\x18\x01 \x01(\x0e\x32\x31.mobile.chats.v2.GetChatInfoStreamResponse.Result\x12(\n\x05\x63hats\x18\x02 \x03(\x0b\x32\x19.common.messaging.v2.Chat\x12R\n\x0f\x66\x61ilure_details\x18\x03 \x03(\x0b\x32\x39.mobile.chats.v2.GetChatInfoStreamResponse.FailureDetails\x1a\xac\x01\n\x0e\x46\x61ilureDetails\x12\"\n\x07\x63hat_id\x18\x01 \x01(\x0b\x32\x11.common.v2.ChatId\x12P\n\x06reason\x18\x02 \x01(\x0e\x32@.mobile.chats.v2.GetChatInfoStreamResponse.FailureDetails.Reason\"$\n\x06Reason\x12\x0b\n\x07UNKNOWN\x10\x00\x12\r\n\tNOT_FOUND\x10\x01\"\x10\n\x06Result\x12\x06\n\x02OK\x10\x00\x32z\n\x08\x43hatInfo\x12n\n\x11GetChatInfoStream\x12).mobile.chats.v2.GetChatInfoStreamRequest\x1a*.mobile.chats.v2.GetChatInfoStreamResponse\"\x00\x30\x01\x42s\n\x14\x63om.kik.gen.chats.v2ZHgithub.com/kikinteractive/xiphias-api-mobile/generated/go/chats/v2;chats\xa2\x02\x10KPBMobileChatsV2b\x06proto3')
  ,
  dependencies=[protobuf__validation__pb2.DESCRIPTOR,common_dot_v2_dot_model__pb2.DESCRIPTOR,messaging_dot_v2_dot_model__pb2.DESCRIPTOR,])
_sym_db.RegisterFileDescriptor(DESCRIPTOR)



_GETCHATINFOSTREAMRESPONSE_FAILUREDETAILS_REASON = _descriptor.EnumDescriptor(
  name='Reason',
  full_name='mobile.chats.v2.GetChatInfoStreamResponse.FailureDetails.Reason',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='UNKNOWN', index=0, number=0,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='NOT_FOUND', index=1, number=1,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=568,
  serialized_end=604,
)
_sym_db.RegisterEnumDescriptor(_GETCHATINFOSTREAMRESPONSE_FAILUREDETAILS_REASON)

_GETCHATINFOSTREAMRESPONSE_RESULT = _descriptor.EnumDescriptor(
  name='Result',
  full_name='mobile.chats.v2.GetChatInfoStreamResponse.Result',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='OK', index=0, number=0,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=606,
  serialized_end=622,
)
_sym_db.RegisterEnumDescriptor(_GETCHATINFOSTREAMRESPONSE_RESULT)


_GETCHATINFOSTREAMREQUEST = _descriptor.Descriptor(
  name='GetChatInfoStreamRequest',
  full_name='mobile.chats.v2.GetChatInfoStreamRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='chat_ids', full_name='mobile.chats.v2.GetChatInfoStreamRequest.chat_ids', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=_descriptor._ParseOptions(descriptor_pb2.FieldOptions(), _b('\312\235%\010\010\001x\001\200\001\200\010'))),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=129,
  serialized_end=206,
)


_GETCHATINFOSTREAMRESPONSE_FAILUREDETAILS = _descriptor.Descriptor(
  name='FailureDetails',
  full_name='mobile.chats.v2.GetChatInfoStreamResponse.FailureDetails',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='chat_id', full_name='mobile.chats.v2.GetChatInfoStreamResponse.FailureDetails.chat_id', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='reason', full_name='mobile.chats.v2.GetChatInfoStreamResponse.FailureDetails.reason', index=1,
      number=2, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
    _GETCHATINFOSTREAMRESPONSE_FAILUREDETAILS_REASON,
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=432,
  serialized_end=604,
)

_GETCHATINFOSTREAMRESPONSE = _descriptor.Descriptor(
  name='GetChatInfoStreamResponse',
  full_name='mobile.chats.v2.GetChatInfoStreamResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='result', full_name='mobile.chats.v2.GetChatInfoStreamResponse.result', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='chats', full_name='mobile.chats.v2.GetChatInfoStreamResponse.chats', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='failure_details', full_name='mobile.chats.v2.GetChatInfoStreamResponse.failure_details', index=2,
      number=3, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[_GETCHATINFOSTREAMRESPONSE_FAILUREDETAILS, ],
  enum_types=[
    _GETCHATINFOSTREAMRESPONSE_RESULT,
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=209,
  serialized_end=622,
)

_GETCHATINFOSTREAMREQUEST.fields_by_name['chat_ids'].message_type = common_dot_v2_dot_model__pb2._CHATID
_GETCHATINFOSTREAMRESPONSE_FAILUREDETAILS.fields_by_name['chat_id'].message_type = common_dot_v2_dot_model__pb2._CHATID
_GETCHATINFOSTREAMRESPONSE_FAILUREDETAILS.fields_by_name['reason'].enum_type = _GETCHATINFOSTREAMRESPONSE_FAILUREDETAILS_REASON
_GETCHATINFOSTREAMRESPONSE_FAILUREDETAILS.containing_type = _GETCHATINFOSTREAMRESPONSE
_GETCHATINFOSTREAMRESPONSE_FAILUREDETAILS_REASON.containing_type = _GETCHATINFOSTREAMRESPONSE_FAILUREDETAILS
_GETCHATINFOSTREAMRESPONSE.fields_by_name['result'].enum_type = _GETCHATINFOSTREAMRESPONSE_RESULT
_GETCHATINFOSTREAMRESPONSE.fields_by_name['chats'].message_type = messaging_dot_v2_dot_model__pb2._CHAT
_GETCHATINFOSTREAMRESPONSE.fields_by_name['failure_details'].message_type = _GETCHATINFOSTREAMRESPONSE_FAILUREDETAILS
_GETCHATINFOSTREAMRESPONSE_RESULT.containing_type = _GETCHATINFOSTREAMRESPONSE
DESCRIPTOR.message_types_by_name['GetChatInfoStreamRequest'] = _GETCHATINFOSTREAMREQUEST
DESCRIPTOR.message_types_by_name['GetChatInfoStreamResponse'] = _GETCHATINFOSTREAMRESPONSE

GetChatInfoStreamRequest = _reflection.GeneratedProtocolMessageType('GetChatInfoStreamRequest', (_message.Message,), dict(
  DESCRIPTOR = _GETCHATINFOSTREAMREQUEST,
  __module__ = 'chats.v2.chat_info_service_pb2'
  # @@protoc_insertion_point(class_scope:mobile.chats.v2.GetChatInfoStreamRequest)
  ))
_sym_db.RegisterMessage(GetChatInfoStreamRequest)

GetChatInfoStreamResponse = _reflection.GeneratedProtocolMessageType('GetChatInfoStreamResponse', (_message.Message,), dict(

  FailureDetails = _reflection.GeneratedProtocolMessageType('FailureDetails', (_message.Message,), dict(
    DESCRIPTOR = _GETCHATINFOSTREAMRESPONSE_FAILUREDETAILS,
    __module__ = 'chats.v2.chat_info_service_pb2'
    # @@protoc_insertion_point(class_scope:mobile.chats.v2.GetChatInfoStreamResponse.FailureDetails)
    ))
  ,
  DESCRIPTOR = _GETCHATINFOSTREAMRESPONSE,
  __module__ = 'chats.v2.chat_info_service_pb2'
  # @@protoc_insertion_point(class_scope:mobile.chats.v2.GetChatInfoStreamResponse)
  ))
_sym_db.RegisterMessage(GetChatInfoStreamResponse)
_sym_db.RegisterMessage(GetChatInfoStreamResponse.FailureDetails)


DESCRIPTOR.has_options = True
DESCRIPTOR._options = _descriptor._ParseOptions(descriptor_pb2.FileOptions(), _b('\n\024com.kik.gen.chats.v2ZHgithub.com/kikinteractive/xiphias-api-mobile/generated/go/chats/v2;chats\242\002\020KPBMobileChatsV2'))
_GETCHATINFOSTREAMREQUEST.fields_by_name['chat_ids'].has_options = True
_GETCHATINFOSTREAMREQUEST.fields_by_name['chat_ids']._options = _descriptor._ParseOptions(descriptor_pb2.FieldOptions(), _b('\312\235%\010\010\001x\001\200\001\200\010'))
# @@protoc_insertion_point(module_scope)
