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

    # hmm: '|'.join(stuff) could be useful!

    # print(('|{:^{}}').format('Organization', offset),
    #       *(('{:^{}}').format(i[0], i[1]) for i in col_lengths),
    #       sep='|', end='|\n')

    col_lengths = [['poo', 7], ['pee', 7], ['Dončić', 7]] # these actually correspond to SequenceMatcher and RBO
    offset = 12

    line_length = offset + sum(i[1] for i in col_lengths) + 2 + len(col_lengths)
    print('-' * line_length)
    header = [['Organization', offset]] + col_lengths
    org_names = b'|'.join(('{:^{}}').format(i[0], i[1]).encode('utf-8') for i in header)
    stdout.flush()
    stdout.buffer.write(b''.join((b'|', org_names, b'|\n')))

    print('-' * line_length)
    sim_measures = [{'d1': .456, 'd2': .789, 'd3': .123}, {'d1': .654, 'd2': .987, 'd3': .321}, {'d1': .5423, 'd2': .164, 'd3': .9765}]

    for draft in sim_measures[0]:
        # org name followed by each similarity score for the mock draft
        # print(('|{:<{}}').format(draft, offset),
        #       *(('{:>{}.3%}').format(m[draft], c_l[1]) for c_l, m in zip(col_lengths, sim_measures)),
        #       sep='|', end='|\n')
        draft_name = ('|{:<{}}').format(draft, offset).encode('utf-8')
        sim_scores = (('{:>{}.3%}').format(m[draft], c_l[1]).encode('utf-8') for c_l, m in zip(col_lengths, sim_measures))
        stdout.flush()
        stdout.buffer.write(b'|'.join((draft_name, *sim_scores, b'\n')))
    print('-' * line_length)

if __name__ == '__main__':
    yes()
