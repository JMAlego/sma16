#!/usr/bin/env node

/*
 *  SMA16.js by Jacob Allen
 *  Tiny little in browser VM 
 */

class Memory {
  constructor() {
    this.memoryBuffer = new ArrayBuffer(2 ** 13);
    this.memoryView = new DataView(this.memoryBuffer);
    this.littleEndian = false;
  }

  get(address) {
    address = address | 0;
    if (address > 2 ** 12 || address < 0)
      throw new Error("Address outside of range");
    return this.memoryView.getUint16(2 * address, this.littleEndian);
  }

  getData(address) {
    return this.get(address) & 0x0fff;
  }

  getInstruction(address) {
    return this.get(address) & 0xf000;
  }

  getShiftedInstruction(address) {
    return this.getInstruction(address) >> 12;
  }

  set(address, value) {
    address = address | 0;
    value = value | 0;
    if (address >= 2 ** 12 || address < 0)
      throw new Error("Address outside of range");
    if (value >= 2 ** 16 || value < 0)
      throw new Error("Value outside of range");
    this.memoryView.setUint16(2 * address, value, this.littleEndian);
  }

  setData(address, value) {
    address = address | 0;
    value = value | 0;
    if (value >= 2 ** 12 || value < 0)
      throw new Error("Value outside of range");
    this.set(address, value | this.getInstruction(address));
  }

  setInstruction(address, value) {
    address = address | 0;
    value = value | 0;
    if (value >= 2 ** 4 || value < 0)
      throw new Error("Value outside of range");
    this.set(address, value << 12 | this.getData(address));
  }

  toString() {
    let result = "Memory {\n";
    for (let index = 0; index < 2 ** 12; index++) {
      const data = this.getData(index);
      const instruction = this.getShiftedInstruction(index);
      if (instruction != 0 || data != 0)
        result += "  " + "0".repeat(3 - index.toString(16).length) + index.toString(16) + ": " + (" ".repeat(5 - InstructionNames[instruction].length) + InstructionNames[instruction]) + "|" + ("0".repeat(3 - data.toString(16).length) + data.toString(16)) + "\n";
    }
    return result + "}";
  }
}

class Register {
  constructor() {
    this.value = 0;
  }

  get() {
    return this.value & 0x0fff;
  }

  set(value) {
    value = value | 0;
    this.value = value & 0x0fff;
  }

  inc(value) {
    value = value | 0;
    this.set(this.get() + value);
  }
}

class Stack {
  constructor(stack_size) {
    this.stack_size = stack_size | 0;
    this.stack = new Uint16Array(this.stack_size);
    this.stack_pointer = 0;
  }

  pop() {
    if (this.stack_pointer == 0)
      return 0;
    else {
      this.stack_pointer--;
      return this.stack[this.stack_pointer];
    }
  }

  push(item) {
    item = item | 0;
    this.stack_pointer++;
    if (this.stack_pointer > this.stack_size) {
      this.stack_pointer = this.stack_size;
      for (let index = 1; index < this.stack_size; index++) {
        this.stack[index - 1] = this.stack[index];
      }
    }
    this.stack[this.stack_pointer - 1] = item;
  }
}

const Instructions = [
  (m) => {
    m.flags = m.flags | 0b10;
  }, // Halt/Data
  (m) => {
    // Free Space
  }, // ???
  (m) => {
    m.pc.set(m.memory.getData(m.pc.get()));
  }, // Jump/Address
  (m) => {
    if (m.flags & 0b01) m.pc.set(m.memory.get(m.pc.get()) & 0xfff);
    else m.pc.inc(1);
  }, // Jump Zero/Address
  (m) => {
    m.accumulator.set(m.memory.getData(m.memory.getData(m.pc.get())));
    m.pc.inc(1);
  }, // Load/Operand
  (m) => {
    m.memory.setData(m.memory.getData(m.pc.get()), m.accumulator.get())
    m.pc.inc(1);
  }, // Store/Operand
  (m) => {
    let data = m.memory.getData(m.pc.get());
    let shift = 12;
    for (; !((1 << (shift - 1)) & data) && shift > 0; shift--);
    m.accumulator.set(m.accumulator.get() << shift);
  }, // Left Shift/Operand
  (m) => {
    let data = m.memory.getData(m.pc.get());
    let shift = 12;
    for (; !((1 << (shift - 1)) & data) && shift > 0; shift--);
    m.accumulator.set(m.accumulator.get() >> shift);
  }, // Right Shift/Operand
  (m) => {
    m.accumulator.set(m.memory.getData(m.pc.get()) ^ m.accumulator.get());
    m.pc.inc(1);
  }, // XOR/Operand
  (m) => {
    m.accumulator.set(m.memory.getData(m.pc.get()) & m.accumulator.get());
    m.pc.inc(1);
  }, // AND/Operand
  (m) => {
    // Free Space
  }, // ???
  (m) => {
    m.accumulator.set(m.accumulator.get() + m.memory.getData(m.pc.get()));
    if (m.accumulator.get() == 0) m.flags |= 0b01;
    else m.flags &= 0b10;
    m.pc.inc(1);
  }, // Add/Operand
  (m) => {
    // Free Space
  }, // ???
  (m) => {
    m.accumulator.set(m.stack.pop());
    m.pc.inc(1);
  }, // Pop/Data
  (m) => {
    m.stack.push(m.accumulator.get());
    m.pc.inc(1);
  }, // Push/Data
  (m) => {
    m.pc.inc(1);
  }  // Noop/Data
];

const InstructionNames = [
  "HALT",
  "FREE",
  "JUMP",
  "JUMPZ",
  "LOAD",
  "STORE",
  "LSHFT",
  "RSHFT",
  "XOR",
  "AND",
  "FREE",
  "ADD",
  "FREE",
  "POP",
  "PUSH",
  "NOOP",
]

class Machine {
  constructor() {
    this.memory = new Memory();
    this.accumulator = new Register();
    this.pc = new Register();
    this.stack = new Stack(12);
    this.flags = 0b00;
  }

  step() {
    this.flags &= 0b01;
    const instruction = Instructions[this.memory.getShiftedInstruction(this.pc.get())];
    instruction.call(this, this);
  }

  run() {
    this.flags &= 0b01;
    while (!(this.flags & 0b10))
      this.step();
  }

  dump(){
    let r = [];
    let i = 2**12;
    while(i>0) if (this.memory.get(--i) != 0) break;
    while(i>=0) r.push(this.memory.get(i--).toString(16)); 
    return "[0x" + r.reverse().join(",0x") + "]"
  }

  load(text, delimiter = "\n") {
    const lines = String(text).split(delimiter);
    let index = 0;
    let labels = {};
    lines.forEach(line => {
      let stored_index = index;
      if (line.startsWith("#")) return;
      let split_line = line.split(" ");
      if (split_line[0] && split_line[0] == ".insert"){
        index = parseInt(split_line[1], 16);
        split_line = split_line.slice(2);
      }
      if (split_line[0] && split_line[0] == ".index"){
        index = parseInt(split_line[1], 16);
        stored_index = index;
        split_line = split_line.slice(2);
      }
      if (split_line[0] && split_line[0].startsWith("@")){
        labels[split_line[0]] = index.toString(16);
        split_line = split_line.slice(1);
      }
      if (line.trim() == "" || split_line.length == 0 || split_line[0] == ""){
        index = stored_index;
        return;
      }
      if (split_line[1].startsWith("@"))
        if (labels[split_line[1]]) split_line[1] = labels[split_line[1]];
        else throw new Error("Label used before definition");
      if(-1 === InstructionNames.indexOf(split_line[0])){
        console.error(split_line[0]);
        throw new Error("No instruction");
      }
      this.memory.setInstruction(index, InstructionNames.indexOf(split_line[0]));
      if (split_line[1].startsWith("+"))
        this.memory.setData(index, index + parseInt(split_line[1].slice(1), 16));
      else if (split_line[1].startsWith("-"))
        this.memory.setData(index, index - parseInt(split_line[1].slice(1), 16));
      else
        this.memory.setData(index, parseInt(split_line[1], 16));
      if(stored_index != index) index = stored_index;
      else index++;
    });
  }
}

if (process && process.argv.length > 2) {
  let test = new Machine();
  test.load(process.argv[2], process.argv[3]);
  console.log(test.dump());
  console.log(test.memory.toString());
  test.run();
  console.log(test.memory.toString());
  //console.log(test);
}else{
  console.log("No input")
}
