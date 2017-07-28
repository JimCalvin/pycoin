import hashlib
import unittest

from ctypes import cdll, byref, c_int, c_uint, c_char_p, c_void_p, c_size_t, create_string_buffer

from pycoin.ecdsa import secp256k1_group, generator_secp256k1, sign, verify, public_pair_for_secret_exponent, deterministic_generate_k
from pycoin.ecdsa.intstream import to_bytes, from_bytes
from pycoin.ecdsa.numbertheory import inverse_mod
from pycoin.ecdsa.native.secp256k1_mp import libsecp256k1, secp256k1, SECP256K1_EC_UNCOMPRESSED
from pycoin.encoding import from_bytes_32, to_bytes_32
from pycoin.intbytes import int2byte, byte2int
from pycoin.serialize import b2h

from pycoin.ecdsa.Secp256k1Group import Group, _p, _a, _b, _Gx, _Gy, _r

legacy_secp256k1_group = Group(_p, _a, _b, (_Gx, _Gy), _r)


class ECDSATestCase(unittest.TestCase):

    def test_infinity(self):
        self.assertEqual(secp256k1_group * 0, secp256k1_group._infinity)
        self.assertEqual(0 * secp256k1_group, secp256k1_group._infinity)

    def test_public_pair_for_secret_exponent(self):
        self.assertEqual(libsecp256k1._public_pair_for_secret_exponent(1), (
            55066263022277343669578718895168534326250603453777594175500187360389116729240,
            32670510020758816978083085130507043184471273380659243275938904335757337482424)
        )
        self.assertEqual(libsecp256k1._public_pair_for_secret_exponent(2), (
            89565891926547004231252920425935692360644145829622209833684329913297188986597,
            12158399299693830322967808612713398636155367887041628176798871954788371653930)
        )
        self.assertEqual(libsecp256k1._public_pair_for_secret_exponent(
                12158399299693830322967808612713398636155367887041628176798871954788371653930), (
            73503477726599187100887421812915680925855587149907858411827017692118332824920,
            27657251006027960104028534670901169416706551781681983309292004861017889370444)
        )

    def test_sign_verify_mutual_compatability(self):
        ctx = libsecp256k1.ctx
        signature = create_string_buffer(64)
        sighash = to_bytes_32(1000)
        secret_key = to_bytes_32(100)

        public_key = create_string_buffer(64)
        r = secp256k1.secp256k1_ec_pubkey_create(ctx, public_key, secret_key)
        self.assertEqual(r, 1)
        self.assertEqual(b2h(public_key),
            '880f50f7ceb4210289266a40b306e33ef52bb75f834c172e65175e3ce2ac3bed'
            '6e2835e3d57ae1fcd0954808be17bd97bf871f7a8a5edadcffcc8812576f7ae5'
        )

        r = secp256k1.secp256k1_ecdsa_sign(ctx, signature, sighash, secret_key, None, None)
        self.assertEqual(r, 1)

        r = secp256k1.secp256k1_ecdsa_verify(ctx, signature, sighash, public_key)
        self.assertEqual(r, 1)

        signature1 = signature[:-1] + int2byte(byte2int(signature[-1]) ^ 1)
        r = secp256k1.secp256k1_ecdsa_verify(ctx, signature1, sighash, public_key)
        self.assertEqual(r, 0)

    def test_sign(self):
        ctx = libsecp256k1.ctx
        sighash = to_bytes_32(1000)
        secret_key = to_bytes_32(100)

        public_key = create_string_buffer(64)
        r = secp256k1.secp256k1_ec_pubkey_create(ctx, public_key, secret_key)
        self.assertEqual(r, 1)
        self.assertEqual(b2h(public_key),
            '880f50f7ceb4210289266a40b306e33ef52bb75f834c172e65175e3ce2ac3bed'
            '6e2835e3d57ae1fcd0954808be17bd97bf871f7a8a5edadcffcc8812576f7ae5'
        )

        signature = create_string_buffer(64)
        r = secp256k1.secp256k1_ecdsa_sign(ctx, signature, sighash, secret_key, None, None)
        self.assertEqual(r, 1)

        compact_signature = create_string_buffer(64)
        secp256k1.secp256k1_ecdsa_signature_serialize_compact(ctx, compact_signature, signature)
        r = from_bytes_32(compact_signature[:32])
        s = from_bytes_32(compact_signature[32:])
        signature = (r, s)

        pubkey_size = c_size_t(65)
        pubkey_serialized = create_string_buffer(65)
        secp256k1.secp256k1_ec_pubkey_serialize(
            ctx, pubkey_serialized, byref(pubkey_size), public_key, SECP256K1_EC_UNCOMPRESSED)
        x = from_bytes_32(pubkey_serialized[1:33])
        y = from_bytes_32(pubkey_serialized[33:])

        legacy_secp256k1_group.verify((x, y), 1000, signature)

    def test_verify(self):
        public_pair = secp256k1_group * 1
        self.assertEqual(public_pair, (
            55066263022277343669578718895168534326250603453777594175500187360389116729240,
            32670510020758816978083085130507043184471273380659243275938904335757337482424)
        )
        hash_value = 1
        sig = (46340862580836590753275244201733144181782255593078084106116359912084275628184,
               81369331955758484632176499244870227132558660296342819670803726373940306621624)
        r = secp256k1_group.verify(public_pair, hash_value, sig)
        self.assertEqual(r, True)


if __name__ == '__main__':
    unittest.main()

