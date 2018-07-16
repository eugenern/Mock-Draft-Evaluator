"""buttspoop"""

from sys import stdout

def yes():
    """poooooooop"""
    # print('Dončić'.encode('utf-8'))
    stdout.buffer.write('Dončić\n'.encode('utf-8'))
    # a = 'Dončić'.encode('utf-8')#.decode('utf-8'))
    # print(b'Don\xc4\x8di\xc4\x87'.decode('utf-8')) #.decode('utf-8'))
    stdout.buffer.write(b'qwer'
                        b'asdf'
                        b'zxcv\n')

    stdout.buffer.write(bytearray(b'pooooooop\n'))

    # stdout.buffer.write(('|{:^{}}').format('Organization', 12).encode('utf-8')
                        # *(('{:^{}}').format(i[0], i[1]).encode('utf-8') for i in [7, 4, 8, 7, 7]))
                        # ('{:^{}}').format('some_org', 8).encode('utf-8'))

                        # hmm: '|'.join(stuff) could be useful!

    col_lengths = [['poo', 7], ['pee', 5], ['asdf', 9]]
    stdout.buffer.write(b'|'.join(('{:^{}}').format(i[0], i[1]).encode('utf-8') for i in col_lengths))

if __name__ == '__main__':
    yes()
