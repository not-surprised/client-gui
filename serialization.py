def serialize(data):
    with open('data.csv', 'w') as f:
        f.write(repr(data))


def deserialize():
    with open('data.csv', 'r') as f:
        text = f.read()
        return eval(text)


if __name__ == '__main__':
    a = [[1., 2., 3.], [4., 5., 6.], [1.23, 4.56, 7.89]]
    serialize(a)
    b = deserialize()
    print(a)
    print(b)
    print(a == b)
