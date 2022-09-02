#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "libgk.h"

uint32_t 
ODF_Encode(Igarashi_Ctx *_Ctx, uint8_t *_Input, uint8_t **_Output, uint32_t _Input_Len, uint32_t _Encoding)
{
  Igarashi_Header *buffer;
  ODF_Buffer_Header *header;
  uint32_t padded_len, buffer_len, header_len;
  uint8_t *temp;

  padded_len = _Input_Len + 0xF & 0xFFFFFF0;                                      // pad the input length to a multiple of 16 bytes by ensuring the first 4 bits are always 0's
  buffer_len = padded_len + 0x10;                                                 // add the header length (16 bytes) to the padded length to get the total size of the buffer
  buffer = (Igarashi_Header *)malloc(buffer_len);
  GK_Fill_Random((uint32_t *)buffer, buffer_len);                                 // initialize bytes with random garbage so the padded bytes at the end of the copied input are "random"
  buffer->encoding_caps[0] = 0x80000004;                                          // the buffer stores enums to indicate the encryption type (which should be constant)
  buffer->encoding_caps[1] = 0x02008000;
  buffer->input_hash = GK_Hash(0, _Input, _Input_Len);                            // and the hash/length of the original input bytes, Hx is 0 for the input
  buffer->input_len = _Input_Len;
  memcpy((uint8_t *)buffer + 0x10, _Input, _Input_Len);                           // copy _Input buffer to the allocated space after the header

  temp = (uint8_t *)malloc(buffer_len);                                           // allocate memory to a possibly unnecessay output pointer
  memset(temp, 0xcc, buffer_len);                                                 // TODO: refector later
  Igarashi_Encrypt_Vb(_Ctx, (uint8_t *)buffer, temp, 0x10);                       // encrypt the 16 bytes in the header
  Igarashi_Encrypt_Vb(_Ctx, (uint8_t *)buffer + 0x10, temp + 0x10, padded_len);   // then it encrypts the copied _Input buffer (and the random padded bytes)

  header_len = buffer_len + 0xE;                                                  // 0xE for the ODF_Buffer_Header, yes there are actually two "headers" in the encrypted output, its weird
  header = (ODF_Buffer_Header *)malloc(header_len);                               // TODO: refactor to cut down on allocations by only allocating once, with space for both headers, then encrypting directly from it...
  header->magic = 0x7FFF817000088B1F;                                             // appears to be constant, possibly an identifier
  header->encoding_flags[0] = 0x4;                                                // this too, oddly enough
  header->encoding_flags[1] = (_Encoding >> 0x18);                                // _Encoding should probably always be 0x2000000 but its not hardcoded, so it's used here as well just in case
  header->buffer_hash = GK_Hash(4, (uint8_t *)buffer, 0x10);                      // Hx is 4 for the buffer header
  memcpy((uint8_t *)header + 0xE, temp, buffer_len);
  free(temp);
  free(buffer);
  // caller must free the output
  *_Output = (uint8_t *)header;
  return header_len;
}

uint32_t 
ODF_Decode(Igarashi_Ctx *_Ctx, uint8_t *_Input, uint8_t **_Output, uint32_t _Input_Len)
{
  ODF_Buffer_Header* header = (ODF_Buffer_Header*)_Input;
  uint8_t* encrypted_data_header = (_Input + 0xE);                              // +14 bytes to get the header of the data
  uint8_t* encrypted_data = (_Input + 0x1E);                                    // +30 bytes is the start of the actual encoded data
  Igarashi_Header data_header;

  if (header->magic != 0x7FFF817000088B1F) {
    printf("\nError: Invalid input header");
    return 0;
  }

  memset(&data_header, 0xcc, 0x10);
  Igarashi_Decrypt_Vb(_Ctx, encrypted_data_header, (uint8_t*)&data_header, 0x10);
  *_Output = (uint8_t *)malloc(_Input_Len - 0x1E);
  // caller must free the output
  Igarashi_Decrypt_Vb(_Ctx, encrypted_data, *_Output, _Input_Len - 0x1E);
  // TODO test to see if the decrypted data has the same gk hash
  return data_header.input_len;
}

uint32_t
LHB_Decode(Takeshi_CBC_Ctx *_Ctx, uint8_t *_Input, uint8_t **Output, uint32_t _Input_Len, uint8_t *_IV)
{
  uint8_t *encrypted_data;
  if (_Input[0] != 0x42) {
    printf("\nInvalid file header\n");
    return 0;
  }
  uint32_t data_len = *(uint32_t*)(_Input + 0x30);
  uint32_t encrypted_len = *(uint32_t*)(_Input + 0x37);
  uint32_t output_len = encrypted_len + 8 & 0xfffffff8;
  *Output = (uint8_t *)malloc(output_len);
  // caller must free the output
  memset(*Output, 0xCC, output_len);

  encrypted_data = (_Input + 0x42); // header + 0x42 is the start of the actual encrypted file
  Takeshi_Decrypt_Cbc(_Ctx, _IV, encrypted_data, *Output, encrypted_len);

  return data_len;
}

void
Igarashi_Expand_Key(Igarashi_Ctx *_Ctx, uint8_t *_Key, uint32_t _Length)
{
  uint32_t a, b, c, d, e, f, g;
  uint32_t i, j, k, l;

  a = 0;
  b = 0;
  c = 0;
  d = 0;
  e = 0;
  f = 0;
  g = 0;

  for (i = 0; i != 18; i += 1) {
    _Ctx->key[i] = _Ctx->key[i] ^ (_Key[(i*4 + 3) % _Length] | _Key[(i*4 + 2) % _Length] << 0x8 | _Key[(i*4 + 1) % _Length] << 0x10 | _Key[i*4 % _Length] << 0x18);
  }
  i = 0;
  for (j = 0; j != 18; j += 2){
    i = i & 0xff | (a & 0xff) << 0x8 | (b & 0xff) << 0x10 | c << 0x18;
    b = d & 0xff | (e & 0xff) << 0x8 | (f & 0xff) << 0x10 | g << 0x18;
    for (l = 0; l != 15; l++){
      e = _Ctx->key[l] ^ i;
      i = (_Ctx->sbox1[e >> 0x10 & 0xff] + _Ctx->sbox0[e >> 0x18] ^ _Ctx->sbox2[e >> 8 & 0xff]) + _Ctx->sbox3[e & 0xff] ^ b;
      b = e;
    }
    i ^= _Ctx->key[15];
    d = (_Ctx->sbox1[i >> 0x10 & 0xff] + _Ctx->sbox0[i >> 0x18] ^ _Ctx->sbox2[i >> 8 & 0xff]) + _Ctx->sbox3[i & 0xff] ^ e ^ _Ctx->key[16];
    i ^= _Ctx->key[17];
    c = i >> 0x18;
    g = d >> 0x18;
    _Ctx->key[j] = i;
    _Ctx->key[(j | 1)] = d;
    b = i >> 0x10;
    a = i >> 0x8;
    f = d >> 0x10;
    e = d >> 0x8;
  }
  for (k = 0; k != 4; k++) {
    for (j = 0; j < 256; j += 2) {
      i = i & 0xff | (a & 0xff) << 8 | (b & 0xff) << 0x10 | c << 0x18;
      b = d & 0xff | (e & 0xff) << 8 | (f & 0xff) << 0x10 | g << 0x18;
      for (l = 0; l != 15; l++) {
        e = _Ctx->key[l] ^ i;
        i = (_Ctx->sbox1[e >> 0x10 & 0xff] + _Ctx->sbox0[e >> 0x18] ^ _Ctx->sbox2[e >> 8 & 0xff]) + _Ctx->sbox3[e & 0xff] ^ b;
        b = e;
      }
      i ^= _Ctx->key[15];
      d = (_Ctx->sbox1[i >> 0x10 & 0xff] + _Ctx->sbox0[i >> 0x18] ^ _Ctx->sbox2[i >> 8 & 0xff]) + _Ctx->sbox3[i & 0xff] ^ e ^ _Ctx->key[16];
      i ^= _Ctx->key[17];
      c = i >> 0x18;
      g = d >> 0x18;
      _Ctx->sbox0[k * 256 + j] = i;
      _Ctx->sbox0[k * 256 + (j | 1)] = d;
      b = i >> 0x10;
      a = i >> 0x8;
      f = d >> 0x10;
      e = d >> 0x8;
    }
  }
}

void
Igarashi_Decrypt_Vb(Igarashi_Ctx *_Ctx, uint8_t *_Input, uint8_t *_Output, uint32_t _Length)
{
  uint32_t a, b, c;
  uint32_t i, j;
  if ((_Length & 7) == 0) {
    if (_Length >> 3 != 0) {
      i = 0;
      do {
        a = (uint32_t)_Input[0] << 0x18 | (uint32_t)_Input[1] << 0x10 | (uint32_t)_Input[2] << 8 | (uint32_t)_Input[3];
        b = (uint32_t)_Input[4] << 0x18 | (uint32_t)_Input[5] << 0x10 | (uint32_t)_Input[6] << 8 | (uint32_t)_Input[7];
        for (j = 17; j > 2; j--) {
          c = _Ctx->key[j] ^ a;
          a = (_Ctx->sbox1[(c >> 0x10 & 0xff)] + _Ctx->sbox0[c >> 0x18] ^ _Ctx->sbox2[(c >> 0x8 & 0xff)]) + _Ctx->sbox3[(c & 0xff)] ^ b;
          b = c;
        }
        a ^= _Ctx->key[2];
        b = (_Ctx->sbox1[(a >> 0x10 & 0xff)] + _Ctx->sbox0[a >> 0x18] ^ _Ctx->sbox2[(a >> 0x8 & 0xff)]) + _Ctx->sbox3[(a & 0xff)] ^ c ^ _Ctx->key[1];
        a ^= _Ctx->key[0];
        _Output[0] = (uint8_t)(a >> 0x18);
        _Output[1] = (uint8_t)(a >> 0x10);
        _Output[2] = (uint8_t)(a >> 0x8);
        _Output[3] = (uint8_t)a;
        _Output[4] = (uint8_t)(b >> 0x18);
        _Output[5] = (uint8_t)(b >> 0x10);
        _Output[6] = (uint8_t)(b >> 0x8);
        _Output[7] = (uint8_t)b;
        _Input = _Input + 0x8;
        _Output = _Output + 0x8;
        i++;
      } while (i != _Length >> 3);
    }
  }
}

void
Igarashi_Encrypt_Vb(Igarashi_Ctx *_Ctx, uint8_t *_Input, uint8_t *_Output, uint32_t _Length)
{
  uint32_t a, b, c;
  uint32_t i, j;
  if ((_Length & 7) == 0) {
    if (_Length >> 3 != 0) {
      i = 0;
      do {
        a = (uint32_t)_Input[0] << 0x18 | (uint32_t)_Input[1] << 0x10 | (uint32_t)_Input[2] << 8 | (uint32_t)_Input[3];
        b = (uint32_t)_Input[4] << 0x18 | (uint32_t)_Input[5] << 0x10 | (uint32_t)_Input[6] << 8 | (uint32_t)_Input[7];
        for (j = 0; j < 15; j++) {
          c = _Ctx->key[j] ^ a;
          a = (_Ctx->sbox1[c >> 0x10 & 0xff] + _Ctx->sbox0[c >> 0x18] ^ _Ctx->sbox2[c >> 8 & 0xff]) + _Ctx->sbox3[c & 0xff] ^ b;
          b = c;
        } 
        a ^= _Ctx->key[15];
        b = (_Ctx->sbox1[a >> 0x10 & 0xff] + _Ctx->sbox0[a >> 0x18] ^ _Ctx->sbox2[a >> 8 & 0xff]) + _Ctx->sbox3[a & 0xff] ^ c ^ _Ctx->key[16];
        a ^= _Ctx->key[17];
        _Output[0] = (uint8_t)(a >> 0x18);
        _Output[1] = (uint8_t)(a >> 0x10);
        _Output[2] = (uint8_t)(a >> 0x8);
        _Output[3] = (uint8_t)a;
        _Output[4] = (uint8_t)(b >> 0x18);
        _Output[5] = (uint8_t)(b >> 0x10);
        _Output[6] = (uint8_t)(b >> 0x8);
        _Output[7] = (uint8_t)b;
        _Input = _Input + 0x8;
        _Output = _Output + 0x8;
        i++;
      } while (i != _Length >> 3);
    }
  }
}

void
Takeshi_Decrypt_Cbc(Takeshi_CBC_Ctx *_Ctx, uint8_t *IV, uint8_t *_Input,uint8_t *_Output, uint32_t _Length)
{
  uint32_t a, b, c, d, e, f, g, h, i, round_cnt;
  uint8_t out_1, out_2, out_3, out_4, out_5, out_6, out_7, out_8, out_9, out_10, out_11, out_12;

  uint32_t *table_a;
  uint32_t *table_b;

  uint64_t input_a, input_b;
  // bafflingly, the IV only affects the first 16 bytes. so, (hypothetically)
  // if you had the wrong iv (which you don't, because you finally figured it out after 3 hours)
  // only the first 16 bytes would be invalid! and the rest would (hypothetically) be perfectly valid!
  if ((_Length & 0xf) == 0) {
    if (_Length == 0) {
      c = 0;
    }
    else {
      do {
        input_a = *(uint64_t *)(_Input + 0x8);
        input_b = *(uint64_t *)_Input;
        round_cnt = _Ctx->round_count;
        a = _Ctx->iv[0] ^ (_Input[0x0] << 0x18 | _Input[0x1] << 0x10 | _Input[0x2] << 8 | _Input[0x3]);
        b = _Ctx->iv[1] ^ (_Input[0x4] << 0x18 | _Input[0x5] << 0x10 | _Input[0x6] << 8 | _Input[0x7]);
        c = _Ctx->iv[2] ^ (_Input[0x8] << 0x18 | _Input[0x9] << 0x10 | _Input[0xA] << 8 | _Input[0xB]);
        d = _Ctx->iv[3] ^ (_Input[0xC] << 0x18 | _Input[0xD] << 0x10 | _Input[0xE] << 8 | _Input[0xF]);
        table_a = _Ctx->table;
        table_b = &_Ctx->table[5];
        if (round_cnt != 0) {
          while(1) {
            round_cnt--;
            e = table_b[-5] ^ a;
            f = table_b[-4] ^ b;
            g =  lookup_a[lookup_c[f >> 0x18]] << 0x18 | lookup_a[lookup_d[f >> 0x10 & 0xff]] << 0x10 | lookup_a[lookup_e[f >> 8 & 0xff]] << 8 | lookup_a[lookup_b[f & 0xff]];
            e = (lookup_a[lookup_c[f >> 0x18]] | g << 8) ^ (lookup_a[lookup_b[e >> 0x18]] << 0x18 | lookup_a[lookup_c[e >> 0x10 & 0xff]] << 0x10 | lookup_a[lookup_d[e >> 8 & 0xff]] << 8 | lookup_a[lookup_e[e & 0xff]]);
            g = g ^ (e >> 0x10 | e << 0x10);
            e = e ^ (g >> 8 | g << 0x18);
            c = g ^ c ^ (e >> 8 | e << 0x18);
            f = e ^ d ^ table_b[-2];
            g = c ^ table_b[-3];
            h =  lookup_a[lookup_c[f >> 0x18]] << 0x18 | lookup_a[lookup_d[f >> 0x10 & 0xff]] << 0x10 | lookup_a[lookup_e[f >> 8 & 0xff]] << 8 | lookup_a[lookup_b[f & 0xff]];
            f = (lookup_a[lookup_c[f >> 0x18]] | h << 8) ^ (lookup_a[lookup_b[g >> 0x18]] << 0x18 | lookup_a[lookup_c[g >> 0x10 & 0xff]] << 0x10 | lookup_a[lookup_d[g >> 8 & 0xff]] << 8 | lookup_a[lookup_e[g & 0xff]]);
            h = h ^ (f >> 0x10 | f << 0x10);
            f = f ^ (h >> 8 | h << 0x18);
            a = h ^ a ^ (f >> 8 | f << 0x18);
            g = a ^ table_b[-1];
            h = f ^ b ^ *table_b;
            i =  lookup_a[lookup_c[h >> 0x18]] << 0x18 | lookup_a[lookup_d[h >> 0x10 & 0xff]] << 0x10 | lookup_a[lookup_e[h >> 8 & 0xff]] << 8 | lookup_a[lookup_b[h & 0xff]];
            g = (lookup_a[lookup_c[h >> 0x18]] | i << 8) ^ (lookup_a[lookup_b[g >> 0x18]] << 0x18 | lookup_a[lookup_c[g >> 0x10 & 0xff]] << 0x10 | lookup_a[lookup_d[g >> 8 & 0xff]] << 8 | lookup_a[lookup_e[g & 0xff]]);
            i = i ^ (g >> 0x10 | g << 0x10);
            g = g ^ (i >> 8 | i << 0x18);
            c = i ^ c ^ (g >> 8 | g << 0x18);
            g = g ^ e ^ d;
            d = c ^ table_b[1];
            e = g ^ table_b[2];
            h =  lookup_a[lookup_c[e >> 0x18]] << 0x18 | lookup_a[lookup_d[e >> 0x10 & 0xff]] << 0x10 | lookup_a[lookup_e[e >> 8 & 0xff]] << 8 | lookup_a[lookup_b[e & 0xff]];
            e = (lookup_a[lookup_c[e >> 0x18]] | h << 8) ^ (lookup_a[lookup_b[d >> 0x18]] << 0x18 | lookup_a[lookup_c[d >> 0x10 & 0xff]] << 0x10 | lookup_a[lookup_d[d >> 8 & 0xff]] << 8 | lookup_a[lookup_e[d & 0xff]]);
            h = h ^ (e >> 0x10 | e << 0x10);
            e = e ^ (h >> 8 | h << 0x18);
            a = h ^ a ^ (e >> 8 | e << 0x18);
            e = e ^ f ^ b;
            b = a ^ table_b[3];
            d = e ^ table_b[4];
            f =  lookup_a[lookup_c[d >> 0x18]] << 0x18 | lookup_a[lookup_d[d >> 0x10 & 0xff]] << 0x10 | lookup_a[lookup_e[d >> 8 & 0xff]] << 8 | lookup_a[lookup_b[d & 0xff]];
            d = (lookup_a[lookup_c[d >> 0x18]] | f << 8) ^ (lookup_a[lookup_b[b >> 0x18]] << 0x18 | lookup_a[lookup_c[b >> 0x10 & 0xff]] << 0x10 | lookup_a[lookup_d[b >> 8 & 0xff]] << 8 | lookup_a[lookup_e[b & 0xff]]);
            f = f ^ (d >> 0x10 | d << 0x10);
            d = d ^ (f >> 8 | f << 0x18);
            c = f ^ c ^ (d >> 8 | d << 0x18);
            d = d ^ g;
            b = c ^ table_b[5];
            f = d ^ table_b[6];
            g =  lookup_a[lookup_c[f >> 0x18]] << 0x18 | lookup_a[lookup_d[f >> 0x10 & 0xff]] << 0x10 | lookup_a[lookup_e[f >> 8 & 0xff]] << 8 | lookup_a[lookup_b[f & 0xff]];
            b = (lookup_a[lookup_c[f >> 0x18]] | g << 8) ^ (lookup_a[lookup_b[b >> 0x18]] << 0x18 | lookup_a[lookup_c[b >> 0x10 & 0xff]] << 0x10 | lookup_a[lookup_d[b >> 8 & 0xff]] << 8 | lookup_a[lookup_e[b & 0xff]]);
            g = g ^ (b >> 0x10 | b << 0x10);
            b = b ^ (g >> 8 | g << 0x18);
            a = g ^ a ^ (b >> 8 | b << 0x18);
            b = b ^ e;
            if (round_cnt == 0) break;
            b = b ^ ((table_b[7] & a) >> 0x1f | (table_b[7] & a) << 1);
            c = (table_b[10] | d) ^ c;
            a = (b | table_b[8]) ^ a;
            d = d ^ ((c & table_b[9]) >> 0x1f | (c & table_b[9]) << 1);
            table_b = table_b + 0x10;
          }
          table_a = table_b + 7;
        }
        c = table_a[0] ^ c;
        b = table_a[3] ^ b;
        d = table_a[1] ^ d;
        a = table_a[2] ^ a;
        out_1 = (uint8_t)(b >> 8);
        _Output[0xe] = out_1;
        _Output[0x3] = (uint8_t)c;
        _Output[0x7] = (uint8_t)d;
        _Output[0xb] = (uint8_t)a;
        _Output[0xf] = (uint8_t)b;
        out_2 = (uint8_t)(c >> 0x18);
        _Output[0] = out_2;
        out_3 = (uint8_t)(c >> 0x10);
        _Output[1] = out_3;
        out_4 = (uint8_t)(c >> 8);
        _Output[2] = out_4;
        out_5 = (uint8_t)(d >> 0x18);
        _Output[4] = out_5;
        out_6 = (uint8_t)(d >> 0x10);
        _Output[5] = out_6;
        out_7 = (uint8_t)(d >> 8);
        _Output[6] = out_7;
        out_8 = (uint8_t)(a >> 0x18);
        _Output[8] = out_8;
        out_9 = (uint8_t)(a >> 0x10);
        _Output[9] = out_9;
        out_10 = (uint8_t)(a >> 8);
        _Output[10] = out_10;
        out_11 = (uint8_t)(b >> 0x18);
        _Output[0xc] = out_11;
        out_12 = (uint8_t)(b >> 0x10);
        _Output[0xd] = out_12;
        _Output[0x0] = IV[0x0] ^ out_2;
        _Output[0x1] = IV[0x1] ^ out_3;
        _Output[0x2] = IV[0x2] ^ out_4;
        _Output[0x3] = IV[0x3] ^ (uint8_t)c;
        _Output[0x4] = IV[0x4] ^ out_5;
        _Output[0x5] = IV[0x5] ^ out_6;
        _Output[0x6] = IV[0x6] ^ out_7;
        _Output[0x7] = IV[0x7] ^ (uint8_t)d;
        _Output[0x8] = IV[0x8] ^ out_8;
        _Output[0x9] = IV[0x9] ^ out_9;
        _Output[0xa] = IV[0xa] ^ out_10;
        _Output[0xb] = IV[0xb] ^ (uint8_t)a;
        _Output[0xc] = IV[0xc] ^ out_11;
        _Output[0xd] = IV[0xd] ^ out_12;
        _Output[0xe] = IV[0xe] ^ out_1;
        _Output[0xf] = IV[0xf] ^ (uint8_t)b;
        _Input = _Input + 0x10;
        _Output = _Output + 0x10;
        _Length = _Length - 0x10;
        *(uint64_t *)(IV + 8) = input_a;
        *(uint64_t *)IV = input_b;
      } while (_Length != 0);
    }
  }
}

uint32_t
GK_Hash(uint32_t Hx,uint8_t *_Input,uint32_t _Length)
{
  int32_t a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, offset;
  uint32_t H1, H2, H3, H4, hashval;
  uint8_t *temp_input;

  if (_Input == NULL) {
      return 0;
  }
  H1 = Hx >> 0x10;
  H2 = Hx & 0xffff;
  if (_Length == 1) {
      H2 = hash_lookup[_Input[0]] + H2;
      H3 = H2 - 0xfff1;
      if (H2 < 0xfff1) {
          H3 = H2;
      }
      H1 = H3 + H1;
      H2 = H1 + 0xf;
      if (H1 < 0xfff1) {
          H2 = H1;
      }
      return H3 | H2 << 0x10;
  }
  if (_Length < 16) {
      if (_Length != 0) {
          do {
              _Length -= 1;
              H2 = _Input[0] + H2;
              H1 = H2 + H1;
              _Input = _Input + 1;
          } while (_Length != 0);
      }
      H3 = H2 - 0xfff1;
      if (H2 < 0xfff1) {
          H3 = H2;
      }
      H1 %= 0xfff1;
      H2 = H3;
      return H2 | H1 << 0x10;
  }
  if (_Length >> 4 < 347) {
Len_lt_347:
    H4 = _Length - 16;
    H3 = H4 & 0xfffffff0;
    temp_input = _Input;
    do {
      p = hash_lookup[temp_input[0x0]] + H2;
      a = hash_lookup[temp_input[0x1]] + p;
      b = hash_lookup[temp_input[0x2]] + a;
      c = hash_lookup[temp_input[0x3]] + b;
      d = hash_lookup[temp_input[0x4]] + c;
      e = hash_lookup[temp_input[0x5]] + d;
      f = hash_lookup[temp_input[0x6]] + e;
      g = hash_lookup[temp_input[0x7]] + f;
      h = hash_lookup[temp_input[0x8]] + g;
      i = hash_lookup[temp_input[0x9]] + h;
      j = hash_lookup[temp_input[0xa]] + i;
      k = hash_lookup[temp_input[0xb]] + j;
      l = hash_lookup[temp_input[0xc]] + k;
      m = hash_lookup[temp_input[0xd]] + l;
      n = hash_lookup[temp_input[0xe]] + m;
      H2 = hash_lookup[temp_input[0xf]] + n;
      H1 = a + b + c + d + e + f + g + h + i + j + k + l + m + n + H1 + H2 + p;
      temp_input += 0x10;
      _Length -= 16;
    } while (_Length > 15);
    _Length = H4 - H3;
    if (_Length == 0) goto final;
    _Input = _Input + H3 + 0x10;
  }
  else {
    while ( _Length >> 4 > 346) {
      offset = 0;
      for (p = -0x15b; p!=0; p++) {
        temp_input = _Input + offset;
        offset += 0x10;
        a = hash_lookup[temp_input[0x0]] + H2;
        b = hash_lookup[temp_input[0x1]] + a;
        c = hash_lookup[temp_input[0x2]] + b;
        d = hash_lookup[temp_input[0x3]] + c;
        e = hash_lookup[temp_input[0x4]] + d;
        f = hash_lookup[temp_input[0x5]] + e;
        g = hash_lookup[temp_input[0x6]] + f;
        h = hash_lookup[temp_input[0x7]] + g;
        i = hash_lookup[temp_input[0x8]] + h;
        j = hash_lookup[temp_input[0x9]] + i;
        k = hash_lookup[temp_input[0xa]] + j;
        l = hash_lookup[temp_input[0xb]] + k;
        m = hash_lookup[temp_input[0xc]] + l;
        n = hash_lookup[temp_input[0xd]] + m;
        o = hash_lookup[temp_input[0xe]] + n;
        H2 = hash_lookup[temp_input[0xf]] + o;
        H1 = a + b + c + d + e + f + g + h + i + j + k + l + m + n + o + H1 + H2;
      }
      _Length -= 5552;
      _Input += 5552;
      H2 %= 0xfff1;
      H1 %= 0xfff1;
    }
    if (_Length == 0) {
      return H2 | H1 << 0x10;
    }
    if (15 < _Length) goto Len_lt_347;
  }
  do {
    _Length -= 1;
    H2 = *_Input + H2;
    H1 = H2 + H1;
    _Input = _Input + 1;
  } while (_Length != 0);
final:
  hashval = H2 % 0xfff1 | (H1 % 0xfff1) * 0x10000;
  //printf("\nGK Hash: 0x%04x", hashval);
  return hashval;
}

void
GK_Fill_Random(uint32_t *_Input, uint32_t _Length)
{
  struct timeval _time;
  uint32_t seed, temp_len, temp_rand, a;
  uint32_t *temp_input;

  gettimeofday(&_time, NULL);
  seed = (uint32_t)((double)_time.tv_usec * 0.001 + (double)_time.tv_sec * 1000.0);
  srand(seed);

  temp_len = _Length & 3;
  if (_Length < 5) {
      temp_len = _Length;
  }
  temp_input = _Input;
  if (4 < _Length) {
      a = _Length >> 2;
      temp_input = _Input + a;
      while (a != 0) {
          temp_rand = rand();
          *_Input = temp_rand;
          // ugly cast to write 2 more "random" bytes with rand() because it only returns two lol
          *((uint16_t *)_Input + 1) = temp_rand ^ temp_rand << 0x1;
          _Input++;
          a--;
      }
  }
  while (temp_len != 0) {
      a = rand();
      *(uint8_t *)temp_input = (uint8_t)a + (uint8_t)(a / 0xff);
      temp_input++;
      temp_len--;
  }
}

#ifdef _WIN32
/* this gettimeofday function probably isnt *strictly* necessary since its just being used as a seed for garbage bytes.
 * so if some kind of compatibility issue arises from this, it could be replaced with another psuedo-random implementation.
 * source: https://git.postgresql.org/gitweb/?p=postgresql.git;a=blob_plain;f=src/port/gettimeofday.c;hb=HEAD
 *
 * gettimeofday.c
 *    Win32 gettimeofday() replacement
 *
 * src/port/gettimeofday.c
 *
 * Copyright (c) 2003 SRA, Inc.
 * Copyright (c) 2003 SKC, Inc.
 *
 * Permission to use, copy, modify, and distribute this software and
 * its documentation for any purpose, without fee, and without a
 * written agreement is hereby granted, provided that the above
 * copyright notice and this paragraph and the following two
 * paragraphs appear in all copies.
 *
 * IN NO EVENT SHALL THE AUTHOR BE LIABLE TO ANY PARTY FOR DIRECT,
 * INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING
 * LOST PROFITS, ARISING OUT OF THE USE OF THIS SOFTWARE AND ITS
 * DOCUMENTATION, EVEN IF THE UNIVERSITY OF CALIFORNIA HAS BEEN ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 * THE AUTHOR SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE.  THE SOFTWARE PROVIDED HEREUNDER IS ON AN "AS
 * IS" BASIS, AND THE AUTHOR HAS NO OBLIGATIONS TO PROVIDE MAINTENANCE,
 * SUPPORT, UPDATES, ENHANCEMENTS, OR MODIFICATIONS.
 */
int
gettimeofday(struct timeval *tp, void *tz) {
    FILETIME    file_time;
    SYSTEMTIME  system_time;
    ULARGE_INTEGER ularge;
    static const uint64_t epoch = 116444736000000000;
    
    GetSystemTime(&system_time);
    SystemTimeToFileTime(&system_time, &file_time);
    ularge.LowPart = file_time.dwLowDateTime;
    ularge.HighPart = file_time.dwHighDateTime;

    tp->tv_sec = (long) ((ularge.QuadPart - epoch) / 10000000L);
    tp->tv_usec = (long) (system_time.wMilliseconds * 1000);

    return 0;
}
#endif