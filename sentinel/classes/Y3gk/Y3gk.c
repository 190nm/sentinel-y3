#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "libgk.h"
#include "structmember.h"

typedef struct _GkIgarashiObject{
  PyObject_HEAD
  Igarashi_Ctx ctx;
} _GkIgarashiObject;

typedef struct _GkTakeshiObject{
  PyObject_HEAD
  Takeshi_CBC_Ctx ctx;
  uint8_t iv[16];
} _GkTakeshiObject;

PyDoc_STRVAR(
  Igarashi_init_doc,
  "Igarashi(/key)\n"
  "--\n\n"
  "Encryption context object used to encrypt/decrypt api requests.\n"
  "\n"
  "Parameters\n"
  "----------\n"
  "``key`` : ``str``\n"
  "  A UTF-8 encoded ``str`` used to initialize the context. Must be exactly 16 bytes long.\n");

PyDoc_STRVAR(
  Igarashi_setkey_doc,
  "setkey($self, /key)\n"
  "--\n\n"
  "Set a  new ``key`` for the context object.\n"
  "\n"
  "Parameters\n"
  "----------\n"
  "``key`` : ``str``\n"
  "  The new ``key`` must also be exactly 16 bytes long\n");

PyDoc_STRVAR(
  Igarashi_encrypt_doc,
  "encrypt($self, /input)\n"
  "--\n\n"
  "Return ``input`` as an encrypted ``bytes`` object.\n"
  "\n"
  "Parameters\n"
  "----------\n"
  "``input`` : ``bytes``\n"
  "Returns\n"
  "-------\n"
  "``encrypted_output`` : ``bytes``\n");

PyDoc_STRVAR(
  Igarashi_decrypt_doc,
  "decrypt($self, /input)\n"
  "--\n\n"
  "Return ``input`` as a decrypted ``bytes`` object.\n"
  "\n"
  "Parameters\n"
  "----------\n"
  "``input`` : ``bytes``\n"
  "Returns\n"
  "-------\n"
  "``decrypted_output`` : ``bytes``\n");

PyDoc_STRVAR(
  Takeshi_init_doc,
  "Takeshi(/iv)\n"
  "--\n\n"
  "Encryption context object used to decrypt assets.\n"
  "\n"
  "Parameters\n"
  "----------\n"
  "``iv`` : ``str``\n"
  "  A UTF-8 encoded ``str`` used to initialize the context. Must be exactly 16 bytes long.\n");

PyDoc_STRVAR(
  Takeshi_decrypt_doc,
  "decrypt($self, /input)\n"
  "--\n\n"
  "Return ``input`` as a decrypted ``bytes`` object.\n"
  "\n"
  "Parameters\n"
  "----------\n"
  "``input`` : ``bytes``\n"
  "Returns\n"
  "-------\n"
  "``decrypted_output`` : ``bytes``\n");

static void
Gk_Igarashi_dealloc (_GkIgarashiObject *self)
{
  Py_TYPE(self)->tp_free((PyObject *) self);
}

static void
Gk_Takeshi_dealloc (_GkTakeshiObject *self)
{
  Py_TYPE(self)->tp_free((PyObject *) self);
}

static PyObject *
Gk_Igarashi_new (PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  _GkIgarashiObject *self;
  self = (_GkIgarashiObject *) type->tp_alloc(type, 0);
  if (self != NULL) {
    memcpy(&self->ctx, &igarashi_ctx_initial, 4168);
  }
  return (PyObject *) self;
}

static PyObject *
Gk_Takeshi_new (PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  _GkTakeshiObject *self;
  self = (_GkTakeshiObject *) type->tp_alloc(type, 0);
  if (self != NULL) {
    memcpy(&self->ctx, &takeshi_cbc_ctx, 280);
  }
  return (PyObject *) self;
}

static int
Gk_Igarashi_init (_GkIgarashiObject *self, PyObject *args, PyObject *kwargs)
{
  static char *keywords[] = {"key", NULL};
  uint8_t *key = NULL;
  Py_ssize_t len;
  if (!PyArg_ParseTupleAndKeywords(args, kwargs, "$s#", keywords, &key, &len))
    return -1;

  if (key) {
    if (len != 16) {
      PyErr_SetString(PyExc_ValueError, "Key must be exactly 16 bytes long.");
      return -1;
    }
    Igarashi_Expand_Key(&self->ctx, key, (uint32_t)len);
  }
  return 0;
}

static int
Gk_Takeshi_init (_GkTakeshiObject *self, PyObject *args, PyObject *kwargs)
{
  static char *keywords[] = {"iv", NULL};
  uint8_t *iv = NULL;
  Py_ssize_t len;
  if (!PyArg_ParseTupleAndKeywords(args, kwargs, "$s#", keywords, &iv, &len))
    return -1;

  if (iv) {
    if (len != 16) {
      PyErr_SetString(PyExc_ValueError, "iv must be exactly 16 bytes long.");
      return -1;
    }
    memcpy(self->iv, iv, 16);
  }
  return 0;
}

static PyObject *
Gk_Igarashi_setkey (_GkIgarashiObject* self, PyObject* args, PyObject* kwargs)
{
  static char* keywords[] = {"key", NULL };
  uint8_t* key = NULL;
  Py_ssize_t len;

  if (!PyArg_ParseTupleAndKeywords(args, kwargs, "$s#", keywords, &key, &len)) {
    return NULL;
  }
  if (key) {
    if (len != 16) {
      PyErr_SetString(PyExc_ValueError, "key must be exactly 16 bytes long.");
      return NULL;
    }
    memcpy(&self->ctx, &igarashi_ctx_initial, 4168);
    Igarashi_Expand_Key(&self->ctx, key, (uint32_t)len);
  }
  Py_RETURN_NONE;
}

static PyObject *
Gk_Igarashi_encrypt (_GkIgarashiObject *self, PyObject *args, PyObject *kwargs)
{
  static char *keywords[] = {"input", NULL};

  uint8_t *input = NULL;
  Py_ssize_t input_len = 0;

  uint8_t *output = NULL;
  Py_ssize_t output_len = 0;
  PyObject* py_output = NULL;

  if(!PyArg_ParseTupleAndKeywords(args, kwargs, "$y#", keywords, &input, &input_len)) {
    return NULL;
  }
  if (input_len >= (UINT32_MAX - 0x2D)){
    PyErr_SetString(PyExc_ValueError, "Not sure why this is happening in the first place, but the input file cannot be larger than ~4.29GB");
    return NULL;
  }
  output_len = ODF_Encode(&self->ctx, input, &output, (uint32_t)input_len, 0x2000000);
  py_output = PyBytes_FromStringAndSize(output, output_len);
  free(output);
  return py_output;
}

static PyObject *
Gk_Igarashi_decrypt(_GkIgarashiObject* self, PyObject* args, PyObject* kwargs)
{
  static char* keywords[] = {"input", NULL };

  uint8_t* input = NULL;
  Py_ssize_t input_len = 0;
  uint8_t* output = NULL;
  Py_ssize_t output_len = 0;
  PyObject* py_output = NULL;

  if (!PyArg_ParseTupleAndKeywords(args, kwargs, "$y#", keywords, &input, &input_len)) {
    return NULL;
  }
  if (input_len >= (UINT32_MAX - 0x2D)){
    PyErr_SetString(PyExc_ValueError, "Not sure why this is happening in the first place, but the input file cannot be larger than ~4.29GB");
    return NULL;
  }
  output_len = ODF_Decode(&self->ctx, input, &output, (uint32_t)input_len);
  py_output = PyBytes_FromStringAndSize(output, output_len);
  free(output);
  return py_output;
}

static PyObject *
Gk_Takeshi_decrypt(_GkTakeshiObject* self, PyObject* args, PyObject* kwargs)
{
  static char* keywords[] = {"input", NULL };

  uint8_t* input = NULL;
  Py_ssize_t input_len = 0;
  uint8_t* output = NULL;
  Py_ssize_t output_len = 0;
  PyObject* py_output = NULL;
  uint8_t iv_temp[16];

  if (!PyArg_ParseTupleAndKeywords(args, kwargs, "$y#", keywords, &input, &input_len)) {
    return NULL;
  }
  if (input_len >= (UINT32_MAX - 0x2D)){
    PyErr_SetString(PyExc_ValueError, "The input file cannot be larger than ~4.29GB. This should hopefully never happen.");
    return NULL;
  }
  memcpy(&iv_temp, self->iv, 16); // yes, the game really does reuse the same iv.
  output_len = LHB_Decode(&self->ctx, input, &output, (uint32_t)input_len, iv_temp);
  if (!output){
    PyErr_SetString(PyExc_ValueError, "Invalid encrypted file header.");
  }
  py_output = PyBytes_FromStringAndSize(output, output_len);
  free(output);
  return py_output;
}


static PyMethodDef 
Gk_IgarashiType_methods[] = {
  {"setkey", (PyCFunction) Gk_Igarashi_setkey, METH_VARARGS | METH_KEYWORDS, Igarashi_setkey_doc},
  {"encrypt", (PyCFunction) Gk_Igarashi_encrypt, METH_VARARGS | METH_KEYWORDS, Igarashi_encrypt_doc},
  {"decrypt", (PyCFunction) Gk_Igarashi_decrypt, METH_VARARGS | METH_KEYWORDS, Igarashi_decrypt_doc},
  {NULL}
};

static PyMethodDef 
Gk_TakeshiType_methods[] = {
  {"decrypt", (PyCFunction) Gk_Takeshi_decrypt, METH_VARARGS | METH_KEYWORDS, Takeshi_decrypt_doc},
  {NULL}
};

static PyTypeObject
IgarashiType = {
  PyVarObject_HEAD_INIT(NULL, 0)
  .tp_name = "Y3gk.Igarashi",
  .tp_doc = Igarashi_init_doc,
  .tp_basicsize = sizeof(_GkIgarashiObject),
  .tp_itemsize = 0,
  .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
  .tp_new = Gk_Igarashi_new,
  .tp_init = (initproc) Gk_Igarashi_init,
  .tp_dealloc = (destructor) Gk_Igarashi_dealloc,
  .tp_methods = Gk_IgarashiType_methods,
};

static PyTypeObject
TakeshiType = {
  PyVarObject_HEAD_INIT(NULL, 0)
  .tp_name = "Y3gk.Takeshi",
  .tp_doc = Takeshi_init_doc,
  .tp_basicsize = sizeof(_GkTakeshiObject),
  .tp_itemsize = 0,
  .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
  .tp_new = Gk_Takeshi_new,
  .tp_init = (initproc) Gk_Takeshi_init,
  .tp_dealloc = (destructor) Gk_Takeshi_dealloc,
  .tp_methods = Gk_TakeshiType_methods,
};


static PyModuleDef
gk = {
  PyModuleDef_HEAD_INIT,
  .m_name = "Y3gk",
  .m_doc = "Python interface for libgk encryption used by yuyuyui.",
  .m_size = -1,
};

PyMODINIT_FUNC
PyInit_Y3gk(void)
{
  PyObject *m;
  if (PyType_Ready(&IgarashiType) < 0)
    return NULL;
  if (PyType_Ready(&TakeshiType) < 0)
    return NULL;
  m = PyModule_Create(&gk);
  if (m == NULL)
    return NULL;

  Py_INCREF(&IgarashiType);
  if (PyModule_AddObject(m, "Igarashi", (PyObject *) &IgarashiType) < 0) {
    Py_DECREF(&IgarashiType);
    Py_DECREF(m);
    return NULL;
  }
  Py_INCREF(&TakeshiType);
  if (PyModule_AddObject(m, "Takeshi", (PyObject *) &TakeshiType) < 0) {
    Py_DECREF(&TakeshiType);
    Py_DECREF(m);
    return NULL;
  }

  return m;
}
