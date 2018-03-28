import itertools

from cytoolz import (
    curry,
    dissoc,
    merge,
    partial,
    pipe,
)
from eth_rlp import (
    HashableRLP,
)
from eth_utils.curried import (
    apply_formatters_to_dict,
    hexstr_if_str,
    to_bytes,
    to_int,
)
import rlp
from rlp.sedes import (
    Binary,
    big_endian_int,
    binary,
)


def serializable_unsigned_transaction_from_dict(transaction_dict):
    filled_transaction = pipe(
        transaction_dict,
        dict,
        partial(merge, TRANSACTION_DEFAULTS),
        chain_id_to_v,
        apply_formatters_to_dict(TRANSACTION_FORMATTERS),
    )
    if 'v' in filled_transaction:
        serializer = Transaction
    else:
        serializer = UnsignedTransaction
    return serializer.from_dict(filled_transaction)


def encode_transaction(unsigned_transaction, vrs):
    (v, r, s) = vrs
    chain_naive_transaction = dissoc(vars(unsigned_transaction), 'v', 'r', 's')
    signed_transaction = Transaction(v=v, r=r, s=s, **chain_naive_transaction)
    return rlp.encode(signed_transaction)


TRANSACTION_DEFAULTS = {
    'value': 0,
    'data': b'',
}

TRANSACTION_FORMATTERS = {
    'nonce': hexstr_if_str(to_int),
    'gasPrice': hexstr_if_str(to_int),
    'gas': hexstr_if_str(to_int),
    'to': hexstr_if_str(to_bytes),
    'value': hexstr_if_str(to_int),
    'data': hexstr_if_str(to_bytes),
    'v': hexstr_if_str(to_int),
    'r': hexstr_if_str(to_int),
    's': hexstr_if_str(to_int),
}


def chain_id_to_v(transaction_dict):
    # See EIP 155
    chain_id = transaction_dict.pop('chainId')
    if chain_id is None:
        return transaction_dict
    else:
        return dict(transaction_dict, v=chain_id, r=0, s=0)


@curry
def fill_transaction_defaults(transaction):
    return merge(TRANSACTION_DEFAULTS, transaction)


class Transaction(HashableRLP):
    fields = (
        ('nonce', big_endian_int),
        ('gasPrice', big_endian_int),
        ('gas', big_endian_int),
        ('to', Binary.fixed_length(20, allow_empty=True)),
        ('value', big_endian_int),
        ('data', binary),
        ('v', big_endian_int),
        ('r', big_endian_int),
        ('s', big_endian_int),
    )


UnsignedTransaction = Transaction.exclude(['v', 'r', 's'])


ChainAwareUnsignedTransaction = Transaction


def strip_signature(txn):
    unsigned_parts = itertools.islice(txn, len(UnsignedTransaction.fields))
    return list(unsigned_parts)


def vrs_from(transaction):
    return (getattr(transaction, part) for part in 'vrs')
