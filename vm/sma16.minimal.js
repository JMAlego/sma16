class M {
  constructor() {
    this.mb = new ArrayBuffer(2 ** 13);
    this.mv = new DataView(this.mb);
    this.li = false;
  }

  g(address) {
    address = address | 0;
    if (address > 2 ** 12 || address < 0)
      throw new Error();
    return this.mv.getUint16(2 * address, this.li);
  }

  gd(address) {
    return this.g(address) & 0x0fff;
  }

  gi(address) {
    return this.g(address) & 0xf000;
  }

  gsi(address) {
    return this.gi(address) >> 12;
  }

  s(address, value) {
    address = address | 0;
    value = value | 0;
    if (address >= 2 ** 12 || address < 0)
      throw new Error();
    if (value >= 2 ** 16 || value < 0)
      throw new Error();
    this.mv.setUint16(2 * address, value, this.li);
  }

  sd(address, value) {
    address = address | 0;
    value = value | 0;
    if (value >= 2 ** 12 || value < 0)
      throw new Error();
    this.s(address, value | this.gi(address));
  }
}

class R {
  constructor() {
    this.value = 0;
  }

  g() {
    return this.value & 0x0fff;
  }

  s(value) {
    value = value | 0;
    this.value = value & 0x0fff;
  }

  i(value) {
    value = value | 0;
    this.s(this.g() + value);
  }
}

class S {
  constructor(stack_size) {
    this.ss = stack_size | 0;
    this.s = new Uint16Array(this.ss);
    this.sp = 0;
  }

  o() {
    if (this.sp == 0)
      return 0;
    else {
      this.sp--;
      return this.s[this.sp];
    }
  }

  u(item) {
    item = item | 0;
    this.sp++;
    if (this.sp > this.ss) {
      this.sp = this.ss;
      for (let index = 1; index < this.ss; index++) {
        this.s[index - 1] = this.s[index];
      }
    }
    this.s[this.sp - 1] = item;
  }
}

const I = [
  (m) => {
    m.f = m.f | 0b10;
  }, // Halt/Data
  (m) => {
    // Free Space
  }, // ???
  (m) => {
    m.p.s(m.m.gd(m.p.g()));
  }, // Jump/Address
  (m) => {
    if (m.f & 0b01) m.p.s(m.m.g(m.p.g()) & 0xfff);
    else m.p.i(1);
  }, // Jump Zero/Address
  (m) => {
    m.a.s(m.m.gd(m.m.gd(m.p.g())));
    m.p.i(1);
  }, // Load/Operand
  (m) => {
    m.m.sd(m.m.gd(m.p.g()), m.a.g())
    m.p.i(1);
  }, // Store/Operand
  (m) => {
    let data = m.m.gd(m.p.g());
    let shift = 12;
    for (; !((1 << (shift - 1)) & data) && shift > 0; shift--);
    m.a.s(m.a.g() << shift);
  }, // Left Shift/Operand
  (m) => {
    let data = m.m.gd(m.p.g());
    let shift = 12;
    for (; !((1 << (shift - 1)) & data) && shift > 0; shift--);
    m.a.s(m.a.g() >> shift);
  }, // Right Shift/Operand
  (m) => {
    m.a.s(m.m.gd(m.p.g()) ^ m.a.g());
    m.p.i(1);
  }, // XOR/Operand
  (m) => {
    m.a.s(m.m.gd(m.p.g()) & m.a.g());
    m.p.i(1);
  }, // AND/Operand
  (m) => {
    // Free Space
  }, // ???
  (m) => {
    m.a.s(m.a.g() + m.m.gd(m.p.g()));
    if (m.a.g() == 0) m.f |= 0b01;
    else m.f &= 0b10;
    m.p.i(1);
  }, // Add/Operand
  (m) => {
    // Free Space
  }, // ???
  (m) => {
    m.a.s(m.s.o());
    m.p.i(1);
  }, // Pop/Data
  (m) => {
    m.s.u(m.a.g());
    m.p.i(1);
  }, // Push/Data
  (m) => {
    m.p.i(1);
  }  // Noop/Data
];

class C {
  constructor() {
    this.m = new M();
    this.a = new R();
    this.p = new R();
    this.s = new S(12);
    this.f = 0b00;
  }

  t() {
    this.f &= 0b01;
    const instruction = I[this.m.gsi(this.p.g())];
    instruction.call(this, this);
  }

  r() {
    this.f &= 0b01;
    while (!(this.f & 0b10))
      this.t();
  }
}

function ex(mem) {
  let t = new C();
  let i = 0;
  for (const key in mem) {
    const element = mem[key];
    t.m.s(i++, element);
  }
  return t;
}
