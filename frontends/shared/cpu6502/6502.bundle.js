var CPU6502 = (() => {
  var __create = Object.create;
  var __defProp = Object.defineProperty;
  var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __getProtoOf = Object.getPrototypeOf;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __commonJS = (cb, mod) => function __require() {
    return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
  };
  var __copyProps = (to, from, except, desc) => {
    if (from && typeof from === "object" || typeof from === "function") {
      for (let key of __getOwnPropNames(from))
        if (!__hasOwnProp.call(to, key) && key !== except)
          __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
    }
    return to;
  };
  var __reExport = (target, mod, secondTarget) => (__copyProps(target, mod, "default"), secondTarget && __copyProps(secondTarget, mod, "default"));
  var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
    // If the importer is in node compatibility mode or this is not an ESM
    // file that has been converted to a CommonJS file using a Babel-
    // compatible transform (i.e. "__esModule" has not been set), then set
    // "default" to the CommonJS "module.exports" for node compatibility.
    isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
    mod
  ));
  var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

  // mat-sz/6502/lib/Utils.js
  var require_Utils = __commonJS({
    "mat-sz/6502/lib/Utils.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      var _1 = require_lib();
      var AddressMode;
      (function(AddressMode2) {
        AddressMode2[AddressMode2["ACCUMULATOR"] = 0] = "ACCUMULATOR";
        AddressMode2[AddressMode2["ABSOLUTE"] = 1] = "ABSOLUTE";
        AddressMode2[AddressMode2["ABSOLUTE_X"] = 2] = "ABSOLUTE_X";
        AddressMode2[AddressMode2["ABSOLUTE_Y"] = 3] = "ABSOLUTE_Y";
        AddressMode2[AddressMode2["IMMEDIATE"] = 4] = "IMMEDIATE";
        AddressMode2[AddressMode2["IMPLIED"] = 5] = "IMPLIED";
        AddressMode2[AddressMode2["INDIRECT"] = 6] = "INDIRECT";
        AddressMode2[AddressMode2["INDIRECT_X"] = 7] = "INDIRECT_X";
        AddressMode2[AddressMode2["INDIRECT_Y"] = 8] = "INDIRECT_Y";
        AddressMode2[AddressMode2["RELATIVE"] = 9] = "RELATIVE";
        AddressMode2[AddressMode2["ZEROPAGE"] = 10] = "ZEROPAGE";
        AddressMode2[AddressMode2["ZEROPAGE_X"] = 11] = "ZEROPAGE_X";
        AddressMode2[AddressMode2["ZEROPAGE_Y"] = 12] = "ZEROPAGE_Y";
      })(AddressMode = exports.AddressMode || (exports.AddressMode = {}));
      exports.getWord = function(state, getMemory, offset) {
        return (getMemory(offset + 1) << 8 | getMemory(offset)) & 65535;
      };
      var getImmediateWord = function(state, getMemory) {
        return exports.getWord(state, getMemory, state.PC + 1);
      };
      var getImmediateByte = function(state, getMemory) {
        return getMemory(state.PC + 1);
      };
      var getAddress = function(state, getMemory, mode) {
        switch (mode) {
          case AddressMode.ABSOLUTE:
            return getImmediateWord(state, getMemory);
          case AddressMode.ABSOLUTE_X:
            return getImmediateWord(state, getMemory) + state.X;
          case AddressMode.ABSOLUTE_Y:
            return getImmediateWord(state, getMemory) + state.Y;
          case AddressMode.INDIRECT:
            return exports.getWord(state, getMemory, getImmediateWord(state, getMemory));
          case AddressMode.INDIRECT_X:
            return exports.getWord(state, getMemory, getImmediateByte(state, getMemory) + state.X & 255);
          case AddressMode.INDIRECT_Y:
            return exports.getWord(state, getMemory, getImmediateByte(state, getMemory)) + state.Y;
          case AddressMode.RELATIVE:
            var value = getImmediateByte(state, getMemory);
            if (value >= 128) {
              value -= 256;
            }
            return state.PC + value;
          case AddressMode.ZEROPAGE:
            return getImmediateByte(state, getMemory);
          case AddressMode.ZEROPAGE_X:
            return getImmediateByte(state, getMemory) + state.X & 255;
          case AddressMode.ZEROPAGE_Y:
            return getImmediateByte(state, getMemory) + state.Y & 255;
          default:
            return 0;
        }
      };
      var getOperand = function(state, getMemory, mode) {
        switch (mode) {
          case AddressMode.ACCUMULATOR:
            return state.A;
          case AddressMode.ABSOLUTE:
          case AddressMode.ABSOLUTE_X:
          case AddressMode.ABSOLUTE_Y:
          case AddressMode.INDIRECT:
          case AddressMode.INDIRECT_X:
          case AddressMode.INDIRECT_Y:
          case AddressMode.RELATIVE:
          case AddressMode.ZEROPAGE:
          case AddressMode.ZEROPAGE_X:
          case AddressMode.ZEROPAGE_Y:
            return getMemory(getAddress(state, getMemory, mode));
          case AddressMode.IMMEDIATE:
            return getImmediateByte(state, getMemory);
          case AddressMode.IMPLIED:
            return 0;
          default:
            return 0;
        }
      };
      var setOperand = function(state, getMemory, setMemory, mode, value) {
        switch (mode) {
          case AddressMode.ACCUMULATOR:
            state.A = value;
            break;
          case AddressMode.ABSOLUTE:
          case AddressMode.ABSOLUTE_X:
          case AddressMode.ABSOLUTE_Y:
          case AddressMode.INDIRECT_X:
          case AddressMode.INDIRECT_Y:
          case AddressMode.ZEROPAGE:
          case AddressMode.ZEROPAGE_X:
          case AddressMode.ZEROPAGE_Y:
            setMemory(getAddress(state, getMemory, mode), value);
            break;
          default:
            throw new Error("Incorrect address mode");
        }
        return state;
      };
      exports.createInstruction = function(fn, addressMode, bytes, cycles) {
        return {
          addressMode,
          bytes,
          cycles,
          name: fn.name ? fn.name : "XYZ",
          fn: function(state, getMemory, setMemory) {
            state.A = state.A & 255;
            state.X = state.X & 255;
            state.Y = state.Y & 255;
            state.SP = state.SP & 255;
            var result = fn(state, {
              address: getAddress(state, getMemory, addressMode),
              operand: getOperand(state, getMemory, addressMode),
              setOperand: function(value) {
                return setOperand(state, getMemory, setMemory, addressMode, value);
              },
              pushByte: function(value) {
                return exports.pushByte(state, setMemory, value);
              },
              pushWord: function(value) {
                return exports.pushWord(state, setMemory, value);
              },
              popByte: function() {
                return exports.popByte(state, getMemory);
              },
              popWord: function() {
                return exports.popWord(state, getMemory);
              },
              performIRQ: function(offset, brk) {
                if (brk === void 0) {
                  brk = false;
                }
                return _1.performIRQ(state, getMemory, setMemory, offset, brk);
              }
            });
            result.PC += bytes;
            result.cycles += cycles;
            return result;
          }
        };
      };
      exports.getSR = function(state, brk) {
        if (brk === void 0) {
          brk = false;
        }
        var value = 0;
        if (state.NF)
          value = value | 128;
        if (state.VF)
          value = value | 64;
        value = value | 32;
        if (brk)
          value = value | 16;
        if (state.DF)
          value = value | 8;
        if (state.IF)
          value = value | 4;
        if (state.ZF)
          value = value | 2;
        if (state.CF)
          value = value | 1;
        return value;
      };
      exports.setSR = function(state, value) {
        state.NF = (value & 128) === 128;
        state.VF = (value & 64) === 64;
        state.DF = (value & 8) === 8;
        state.IF = (value & 4) === 4;
        state.ZF = (value & 2) === 2;
        state.CF = (value & 1) === 1;
        return state;
      };
      exports.pushByte = function(state, setMemory, value) {
        setMemory(256 | state.SP, value);
        state.SP--;
        return state;
      };
      exports.pushWord = function(state, setMemory, value) {
        setMemory(256 | state.SP, value >> 8);
        setMemory(256 | state.SP - 1, value & 255);
        state.SP -= 2;
        return state;
      };
      exports.popByte = function(state, getMemory) {
        state.SP++;
        return getMemory(256 | state.SP);
      };
      exports.popWord = function(state, getMemory) {
        state.SP += 2;
        return getMemory(256 | state.SP) << 8 | getMemory(256 | state.SP - 1) & 65535;
      };
      exports.decodeBCD = function(operand) {
        return (operand >> 4) * 10 + (operand & 15);
      };
      exports.encodeBCD = function(value) {
        return (Math.floor(value / 10) << 4) + value % 10;
      };
    }
  });

  // mat-sz/6502/lib/instructions/ADC.js
  var require_ADC = __commonJS({
    "mat-sz/6502/lib/instructions/ADC.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      var Utils_1 = require_Utils();
      function ADC(state, _a) {
        var operand = _a.operand;
        var value = 0;
        if (state.DF) {
          value = Utils_1.decodeBCD(state.A) + Utils_1.decodeBCD(operand);
          if (state.CF)
            value++;
          state.CF = value > 99;
          if (value > 99)
            value -= 100;
          state.ZF = value === 0;
          value = Utils_1.encodeBCD(value);
          state.NF = value > 127;
        } else {
          value = state.A + operand;
          if (state.CF)
            value++;
          state.CF = value > 255;
          state.ZF = (value & 255) === 0;
          state.NF = (value & 128) === 128;
          state.VF = (~(state.A ^ operand) & (state.A ^ value) & 128) !== 0;
        }
        state.A = value;
        return state;
      }
      exports.default = ADC;
    }
  });

  // mat-sz/6502/lib/instructions/ASL.js
  var require_ASL = __commonJS({
    "mat-sz/6502/lib/instructions/ASL.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function ASL(state, _a) {
        var operand = _a.operand, setOperand = _a.setOperand;
        state.CF = operand >= 128;
        var value = operand << 1;
        state.ZF = (value & 255) === 0;
        state.NF = (value & 128) === 128;
        setOperand(value);
        return state;
      }
      exports.default = ASL;
    }
  });

  // mat-sz/6502/lib/instructions/AND.js
  var require_AND = __commonJS({
    "mat-sz/6502/lib/instructions/AND.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function AND(state, _a) {
        var operand = _a.operand;
        var value = state.A & operand;
        state.ZF = (value & 255) === 0;
        state.NF = (value & 128) === 128;
        state.A = value;
        return state;
      }
      exports.default = AND;
    }
  });

  // mat-sz/6502/lib/instructions/BCC.js
  var require_BCC = __commonJS({
    "mat-sz/6502/lib/instructions/BCC.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function BCC(state, _a) {
        var address = _a.address;
        if (!state.CF) {
          state.PC = address;
        }
        return state;
      }
      exports.default = BCC;
    }
  });

  // mat-sz/6502/lib/instructions/BCS.js
  var require_BCS = __commonJS({
    "mat-sz/6502/lib/instructions/BCS.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function BCS(state, _a) {
        var address = _a.address;
        if (state.CF) {
          state.PC = address;
        }
        return state;
      }
      exports.default = BCS;
    }
  });

  // mat-sz/6502/lib/instructions/BEQ.js
  var require_BEQ = __commonJS({
    "mat-sz/6502/lib/instructions/BEQ.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function BEQ(state, _a) {
        var address = _a.address;
        if (state.ZF) {
          state.PC = address;
        }
        return state;
      }
      exports.default = BEQ;
    }
  });

  // mat-sz/6502/lib/instructions/BMI.js
  var require_BMI = __commonJS({
    "mat-sz/6502/lib/instructions/BMI.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function BMI(state, _a) {
        var address = _a.address;
        if (state.NF) {
          state.PC = address;
        }
        return state;
      }
      exports.default = BMI;
    }
  });

  // mat-sz/6502/lib/instructions/BNE.js
  var require_BNE = __commonJS({
    "mat-sz/6502/lib/instructions/BNE.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function BNE(state, _a) {
        var address = _a.address;
        if (!state.ZF) {
          state.PC = address;
        }
        return state;
      }
      exports.default = BNE;
    }
  });

  // mat-sz/6502/lib/instructions/BPL.js
  var require_BPL = __commonJS({
    "mat-sz/6502/lib/instructions/BPL.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function BPL(state, _a) {
        var address = _a.address;
        if (!state.NF) {
          state.PC = address;
        }
        return state;
      }
      exports.default = BPL;
    }
  });

  // mat-sz/6502/lib/instructions/BVC.js
  var require_BVC = __commonJS({
    "mat-sz/6502/lib/instructions/BVC.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function BVC(state, _a) {
        var address = _a.address;
        if (!state.VF) {
          state.PC = address;
        }
        return state;
      }
      exports.default = BVC;
    }
  });

  // mat-sz/6502/lib/instructions/BVS.js
  var require_BVS = __commonJS({
    "mat-sz/6502/lib/instructions/BVS.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function BVS(state, _a) {
        var address = _a.address;
        if (state.VF) {
          state.PC = address;
        }
        return state;
      }
      exports.default = BVS;
    }
  });

  // mat-sz/6502/lib/instructions/BIT.js
  var require_BIT = __commonJS({
    "mat-sz/6502/lib/instructions/BIT.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function BIT(state, _a) {
        var operand = _a.operand;
        var value = state.A & operand;
        state.NF = (operand & 128) === 128;
        state.VF = (operand & 64) === 64;
        state.ZF = (value & 255) === 0;
        return state;
      }
      exports.default = BIT;
    }
  });

  // mat-sz/6502/lib/instructions/BRK.js
  var require_BRK = __commonJS({
    "mat-sz/6502/lib/instructions/BRK.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function BRK(state, _a) {
        var performIRQ = _a.performIRQ;
        state.PC += 2;
        performIRQ(65534, true);
        return state;
      }
      exports.default = BRK;
    }
  });

  // mat-sz/6502/lib/instructions/CLC.js
  var require_CLC = __commonJS({
    "mat-sz/6502/lib/instructions/CLC.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function CLC(state) {
        state.CF = false;
        return state;
      }
      exports.default = CLC;
    }
  });

  // mat-sz/6502/lib/instructions/CLD.js
  var require_CLD = __commonJS({
    "mat-sz/6502/lib/instructions/CLD.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function CLD(state) {
        state.DF = false;
        return state;
      }
      exports.default = CLD;
    }
  });

  // mat-sz/6502/lib/instructions/CLI.js
  var require_CLI = __commonJS({
    "mat-sz/6502/lib/instructions/CLI.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function CLI(state) {
        state.IF = false;
        return state;
      }
      exports.default = CLI;
    }
  });

  // mat-sz/6502/lib/instructions/CLV.js
  var require_CLV = __commonJS({
    "mat-sz/6502/lib/instructions/CLV.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function CLV(state) {
        state.VF = false;
        return state;
      }
      exports.default = CLV;
    }
  });

  // mat-sz/6502/lib/instructions/CMP.js
  var require_CMP = __commonJS({
    "mat-sz/6502/lib/instructions/CMP.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function CMP(state, _a) {
        var operand = _a.operand;
        var value = state.A - operand;
        state.CF = state.A >= operand;
        state.ZF = state.A === operand;
        state.NF = (value & 128) === 128;
        return state;
      }
      exports.default = CMP;
    }
  });

  // mat-sz/6502/lib/instructions/CPX.js
  var require_CPX = __commonJS({
    "mat-sz/6502/lib/instructions/CPX.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function CPX(state, _a) {
        var operand = _a.operand;
        var value = state.X - operand;
        state.CF = state.X >= operand;
        state.ZF = state.X === operand;
        state.NF = (value & 128) === 128;
        return state;
      }
      exports.default = CPX;
    }
  });

  // mat-sz/6502/lib/instructions/CPY.js
  var require_CPY = __commonJS({
    "mat-sz/6502/lib/instructions/CPY.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function CPY(state, _a) {
        var operand = _a.operand;
        var value = state.Y - operand;
        state.CF = state.Y >= operand;
        state.ZF = state.Y === operand;
        state.NF = (value & 128) === 128;
        return state;
      }
      exports.default = CPY;
    }
  });

  // mat-sz/6502/lib/instructions/DEC.js
  var require_DEC = __commonJS({
    "mat-sz/6502/lib/instructions/DEC.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function DEC(state, _a) {
        var operand = _a.operand, setOperand = _a.setOperand;
        var value = operand - 1;
        state.ZF = (value & 255) === 0;
        state.NF = (value & 128) === 128;
        setOperand(value);
        return state;
      }
      exports.default = DEC;
    }
  });

  // mat-sz/6502/lib/instructions/DEX.js
  var require_DEX = __commonJS({
    "mat-sz/6502/lib/instructions/DEX.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function DEX(state, _a) {
        var operand = _a.operand;
        state.X--;
        state.ZF = (state.X & 255) === 0;
        state.NF = (state.X & 128) === 128;
        return state;
      }
      exports.default = DEX;
    }
  });

  // mat-sz/6502/lib/instructions/DEY.js
  var require_DEY = __commonJS({
    "mat-sz/6502/lib/instructions/DEY.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function DEY(state, _a) {
        var operand = _a.operand;
        state.Y--;
        state.ZF = (state.Y & 255) === 0;
        state.NF = (state.Y & 128) === 128;
        return state;
      }
      exports.default = DEY;
    }
  });

  // mat-sz/6502/lib/instructions/INC.js
  var require_INC = __commonJS({
    "mat-sz/6502/lib/instructions/INC.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function INC(state, _a) {
        var operand = _a.operand, setOperand = _a.setOperand;
        var value = operand + 1;
        state.ZF = (value & 255) === 0;
        state.NF = (value & 128) === 128;
        setOperand(value);
        return state;
      }
      exports.default = INC;
    }
  });

  // mat-sz/6502/lib/instructions/INX.js
  var require_INX = __commonJS({
    "mat-sz/6502/lib/instructions/INX.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function INX(state) {
        state.X++;
        state.ZF = (state.X & 255) === 0;
        state.NF = (state.X & 128) === 128;
        return state;
      }
      exports.default = INX;
    }
  });

  // mat-sz/6502/lib/instructions/INY.js
  var require_INY = __commonJS({
    "mat-sz/6502/lib/instructions/INY.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function INY(state) {
        state.Y++;
        state.ZF = (state.Y & 255) === 0;
        state.NF = (state.Y & 128) === 128;
        return state;
      }
      exports.default = INY;
    }
  });

  // mat-sz/6502/lib/instructions/EOR.js
  var require_EOR = __commonJS({
    "mat-sz/6502/lib/instructions/EOR.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function EOR(state, _a) {
        var operand = _a.operand;
        var value = state.A ^ operand;
        state.ZF = (value & 255) === 0;
        state.NF = (value & 128) === 128;
        state.A = value;
        return state;
      }
      exports.default = EOR;
    }
  });

  // mat-sz/6502/lib/instructions/ORA.js
  var require_ORA = __commonJS({
    "mat-sz/6502/lib/instructions/ORA.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function ORA(state, _a) {
        var operand = _a.operand;
        var value = state.A | operand;
        state.ZF = (value & 255) === 0;
        state.NF = (value & 128) === 128;
        state.A = value;
        return state;
      }
      exports.default = ORA;
    }
  });

  // mat-sz/6502/lib/instructions/JMP.js
  var require_JMP = __commonJS({
    "mat-sz/6502/lib/instructions/JMP.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function JMP(state, _a) {
        var address = _a.address;
        state.PC = address;
        return state;
      }
      exports.default = JMP;
    }
  });

  // mat-sz/6502/lib/instructions/JSR.js
  var require_JSR = __commonJS({
    "mat-sz/6502/lib/instructions/JSR.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function JSR(state, _a) {
        var address = _a.address, pushWord = _a.pushWord;
        pushWord(state.PC + 2);
        state.PC = address;
        return state;
      }
      exports.default = JSR;
    }
  });

  // mat-sz/6502/lib/instructions/RTI.js
  var require_RTI = __commonJS({
    "mat-sz/6502/lib/instructions/RTI.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      var Utils_1 = require_Utils();
      function RTI(state, _a) {
        var popByte = _a.popByte, popWord = _a.popWord;
        state = Utils_1.setSR(state, popByte());
        state.PC = popWord() - 1;
        return state;
      }
      exports.default = RTI;
    }
  });

  // mat-sz/6502/lib/instructions/RTS.js
  var require_RTS = __commonJS({
    "mat-sz/6502/lib/instructions/RTS.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function RTS(state, _a) {
        var popWord = _a.popWord;
        state.PC = popWord();
        return state;
      }
      exports.default = RTS;
    }
  });

  // mat-sz/6502/lib/instructions/PHA.js
  var require_PHA = __commonJS({
    "mat-sz/6502/lib/instructions/PHA.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function PHA(state, _a) {
        var pushByte = _a.pushByte;
        pushByte(state.A);
        return state;
      }
      exports.default = PHA;
    }
  });

  // mat-sz/6502/lib/instructions/PHP.js
  var require_PHP = __commonJS({
    "mat-sz/6502/lib/instructions/PHP.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      var Utils_1 = require_Utils();
      function PHP(state, _a) {
        var pushByte = _a.pushByte;
        pushByte(Utils_1.getSR(state, true));
        return state;
      }
      exports.default = PHP;
    }
  });

  // mat-sz/6502/lib/instructions/PLA.js
  var require_PLA = __commonJS({
    "mat-sz/6502/lib/instructions/PLA.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function PLA(state, _a) {
        var popByte = _a.popByte;
        state.A = popByte();
        state.ZF = (state.A & 255) === 0;
        state.NF = (state.A & 128) === 128;
        return state;
      }
      exports.default = PLA;
    }
  });

  // mat-sz/6502/lib/instructions/PLP.js
  var require_PLP = __commonJS({
    "mat-sz/6502/lib/instructions/PLP.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      var Utils_1 = require_Utils();
      function PLP(state, _a) {
        var popByte = _a.popByte;
        return Utils_1.setSR(state, popByte());
      }
      exports.default = PLP;
    }
  });

  // mat-sz/6502/lib/instructions/LDA.js
  var require_LDA = __commonJS({
    "mat-sz/6502/lib/instructions/LDA.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function LDA(state, _a) {
        var operand = _a.operand;
        state.A = operand;
        state.ZF = (state.A & 255) === 0;
        state.NF = (state.A & 128) === 128;
        return state;
      }
      exports.default = LDA;
    }
  });

  // mat-sz/6502/lib/instructions/LDX.js
  var require_LDX = __commonJS({
    "mat-sz/6502/lib/instructions/LDX.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function LDX(state, _a) {
        var operand = _a.operand;
        state.X = operand;
        state.ZF = (state.X & 255) === 0;
        state.NF = (state.X & 128) === 128;
        return state;
      }
      exports.default = LDX;
    }
  });

  // mat-sz/6502/lib/instructions/LDY.js
  var require_LDY = __commonJS({
    "mat-sz/6502/lib/instructions/LDY.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function LDY(state, _a) {
        var operand = _a.operand;
        state.Y = operand;
        state.ZF = (state.Y & 255) === 0;
        state.NF = (state.Y & 128) === 128;
        return state;
      }
      exports.default = LDY;
    }
  });

  // mat-sz/6502/lib/instructions/STA.js
  var require_STA = __commonJS({
    "mat-sz/6502/lib/instructions/STA.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function STA(state, _a) {
        var setOperand = _a.setOperand;
        setOperand(state.A);
        return state;
      }
      exports.default = STA;
    }
  });

  // mat-sz/6502/lib/instructions/STX.js
  var require_STX = __commonJS({
    "mat-sz/6502/lib/instructions/STX.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function STX(state, _a) {
        var setOperand = _a.setOperand;
        setOperand(state.X);
        return state;
      }
      exports.default = STX;
    }
  });

  // mat-sz/6502/lib/instructions/STY.js
  var require_STY = __commonJS({
    "mat-sz/6502/lib/instructions/STY.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function STY(state, _a) {
        var setOperand = _a.setOperand;
        setOperand(state.Y);
        return state;
      }
      exports.default = STY;
    }
  });

  // mat-sz/6502/lib/instructions/NOP.js
  var require_NOP = __commonJS({
    "mat-sz/6502/lib/instructions/NOP.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function NOP(state) {
        return state;
      }
      exports.default = NOP;
    }
  });

  // mat-sz/6502/lib/instructions/TAX.js
  var require_TAX = __commonJS({
    "mat-sz/6502/lib/instructions/TAX.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function TAX(state) {
        state.X = state.A;
        state.ZF = (state.X & 255) === 0;
        state.NF = (state.X & 128) === 128;
        return state;
      }
      exports.default = TAX;
    }
  });

  // mat-sz/6502/lib/instructions/TAY.js
  var require_TAY = __commonJS({
    "mat-sz/6502/lib/instructions/TAY.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function TAY(state) {
        state.Y = state.A;
        state.ZF = (state.Y & 255) === 0;
        state.NF = (state.Y & 128) === 128;
        return state;
      }
      exports.default = TAY;
    }
  });

  // mat-sz/6502/lib/instructions/TSX.js
  var require_TSX = __commonJS({
    "mat-sz/6502/lib/instructions/TSX.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function TSX(state) {
        state.X = state.SP;
        state.ZF = (state.X & 255) === 0;
        state.NF = (state.X & 128) === 128;
        return state;
      }
      exports.default = TSX;
    }
  });

  // mat-sz/6502/lib/instructions/TXA.js
  var require_TXA = __commonJS({
    "mat-sz/6502/lib/instructions/TXA.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function TXA(state) {
        state.A = state.X;
        state.ZF = (state.A & 255) === 0;
        state.NF = (state.A & 128) === 128;
        return state;
      }
      exports.default = TXA;
    }
  });

  // mat-sz/6502/lib/instructions/TXS.js
  var require_TXS = __commonJS({
    "mat-sz/6502/lib/instructions/TXS.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function TXS(state) {
        state.SP = state.X;
        return state;
      }
      exports.default = TXS;
    }
  });

  // mat-sz/6502/lib/instructions/TYA.js
  var require_TYA = __commonJS({
    "mat-sz/6502/lib/instructions/TYA.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function TYA(state) {
        state.A = state.Y;
        state.ZF = (state.A & 255) === 0;
        state.NF = (state.A & 128) === 128;
        return state;
      }
      exports.default = TYA;
    }
  });

  // mat-sz/6502/lib/instructions/LSR.js
  var require_LSR = __commonJS({
    "mat-sz/6502/lib/instructions/LSR.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function LSR(state, _a) {
        var operand = _a.operand, setOperand = _a.setOperand;
        state.CF = (operand & 1) === 1;
        var value = operand >> 1;
        state.ZF = (value & 255) === 0;
        state.NF = (value & 128) === 128;
        setOperand(value);
        return state;
      }
      exports.default = LSR;
    }
  });

  // mat-sz/6502/lib/instructions/SBC.js
  var require_SBC = __commonJS({
    "mat-sz/6502/lib/instructions/SBC.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      var Utils_1 = require_Utils();
      function SBC(state, _a) {
        var operand = _a.operand;
        var value = 0;
        if (state.DF) {
          value = Utils_1.decodeBCD(state.A) - Utils_1.decodeBCD(operand);
          if (!state.CF)
            value--;
          state.CF = value >= 0;
          if (value < 0)
            value += 100;
          state.ZF = value === 0;
          value = Utils_1.encodeBCD(value);
          state.NF = value > 127;
        } else {
          value = state.A + ~operand;
          if (state.CF)
            value++;
          state.CF = state.A + (state.CF ? 1 : 0) > operand;
          state.ZF = (value & 255) === 0;
          state.NF = (value & 128) === 128;
          state.VF = (~(state.A ^ ~operand) & (state.A ^ value) & 128) !== 0;
        }
        state.A = value;
        return state;
      }
      exports.default = SBC;
    }
  });

  // mat-sz/6502/lib/instructions/ROL.js
  var require_ROL = __commonJS({
    "mat-sz/6502/lib/instructions/ROL.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function ROL(state, _a) {
        var operand = _a.operand, setOperand = _a.setOperand;
        var value = operand << 1;
        if (state.CF)
          value = value | 1;
        state.ZF = (value & 255) === 0;
        state.NF = (value & 128) === 128;
        state.CF = operand >= 128;
        setOperand(value);
        return state;
      }
      exports.default = ROL;
    }
  });

  // mat-sz/6502/lib/instructions/ROR.js
  var require_ROR = __commonJS({
    "mat-sz/6502/lib/instructions/ROR.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function ROR(state, _a) {
        var operand = _a.operand, setOperand = _a.setOperand;
        var value = operand >> 1;
        if (state.CF)
          value = value | 128;
        state.ZF = (value & 255) === 0;
        state.NF = (value & 128) === 128;
        state.CF = (operand & 1) === 1;
        setOperand(value);
        return state;
      }
      exports.default = ROR;
    }
  });

  // mat-sz/6502/lib/instructions/SEC.js
  var require_SEC = __commonJS({
    "mat-sz/6502/lib/instructions/SEC.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function SEC(state) {
        state.CF = true;
        return state;
      }
      exports.default = SEC;
    }
  });

  // mat-sz/6502/lib/instructions/SED.js
  var require_SED = __commonJS({
    "mat-sz/6502/lib/instructions/SED.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function SED(state) {
        state.DF = true;
        return state;
      }
      exports.default = SED;
    }
  });

  // mat-sz/6502/lib/instructions/SEI.js
  var require_SEI = __commonJS({
    "mat-sz/6502/lib/instructions/SEI.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      function SEI(state) {
        state.IF = true;
        return state;
      }
      exports.default = SEI;
    }
  });

  // mat-sz/6502/lib/instructionSet.js
  var require_instructionSet = __commonJS({
    "mat-sz/6502/lib/instructionSet.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      var Utils_1 = require_Utils();
      var ADC_1 = require_ADC();
      var ASL_1 = require_ASL();
      var AND_1 = require_AND();
      var BCC_1 = require_BCC();
      var BCS_1 = require_BCS();
      var BEQ_1 = require_BEQ();
      var BMI_1 = require_BMI();
      var BNE_1 = require_BNE();
      var BPL_1 = require_BPL();
      var BVC_1 = require_BVC();
      var BVS_1 = require_BVS();
      var BIT_1 = require_BIT();
      var BRK_1 = require_BRK();
      var CLC_1 = require_CLC();
      var CLD_1 = require_CLD();
      var CLI_1 = require_CLI();
      var CLV_1 = require_CLV();
      var CMP_1 = require_CMP();
      var CPX_1 = require_CPX();
      var CPY_1 = require_CPY();
      var DEC_1 = require_DEC();
      var DEX_1 = require_DEX();
      var DEY_1 = require_DEY();
      var INC_1 = require_INC();
      var INX_1 = require_INX();
      var INY_1 = require_INY();
      var EOR_1 = require_EOR();
      var ORA_1 = require_ORA();
      var JMP_1 = require_JMP();
      var JSR_1 = require_JSR();
      var RTI_1 = require_RTI();
      var RTS_1 = require_RTS();
      var PHA_1 = require_PHA();
      var PHP_1 = require_PHP();
      var PLA_1 = require_PLA();
      var PLP_1 = require_PLP();
      var LDA_1 = require_LDA();
      var LDX_1 = require_LDX();
      var LDY_1 = require_LDY();
      var STA_1 = require_STA();
      var STX_1 = require_STX();
      var STY_1 = require_STY();
      var NOP_1 = require_NOP();
      var TAX_1 = require_TAX();
      var TAY_1 = require_TAY();
      var TSX_1 = require_TSX();
      var TXA_1 = require_TXA();
      var TXS_1 = require_TXS();
      var TYA_1 = require_TYA();
      var LSR_1 = require_LSR();
      var SBC_1 = require_SBC();
      var ROL_1 = require_ROL();
      var ROR_1 = require_ROR();
      var SEC_1 = require_SEC();
      var SED_1 = require_SED();
      var SEI_1 = require_SEI();
      var instructionSet = [];
      instructionSet[105] = Utils_1.createInstruction(ADC_1.default, Utils_1.AddressMode.IMMEDIATE, 2, 2);
      instructionSet[101] = Utils_1.createInstruction(ADC_1.default, Utils_1.AddressMode.ZEROPAGE, 2, 3);
      instructionSet[117] = Utils_1.createInstruction(ADC_1.default, Utils_1.AddressMode.ZEROPAGE_X, 2, 4);
      instructionSet[109] = Utils_1.createInstruction(ADC_1.default, Utils_1.AddressMode.ABSOLUTE, 3, 4);
      instructionSet[125] = Utils_1.createInstruction(ADC_1.default, Utils_1.AddressMode.ABSOLUTE_X, 3, 4);
      instructionSet[121] = Utils_1.createInstruction(ADC_1.default, Utils_1.AddressMode.ABSOLUTE_Y, 3, 4);
      instructionSet[97] = Utils_1.createInstruction(ADC_1.default, Utils_1.AddressMode.INDIRECT_X, 2, 6);
      instructionSet[113] = Utils_1.createInstruction(ADC_1.default, Utils_1.AddressMode.INDIRECT_Y, 2, 5);
      instructionSet[41] = Utils_1.createInstruction(AND_1.default, Utils_1.AddressMode.IMMEDIATE, 2, 2);
      instructionSet[37] = Utils_1.createInstruction(AND_1.default, Utils_1.AddressMode.ZEROPAGE, 2, 3);
      instructionSet[53] = Utils_1.createInstruction(AND_1.default, Utils_1.AddressMode.ZEROPAGE_X, 2, 4);
      instructionSet[45] = Utils_1.createInstruction(AND_1.default, Utils_1.AddressMode.ABSOLUTE, 3, 4);
      instructionSet[61] = Utils_1.createInstruction(AND_1.default, Utils_1.AddressMode.ABSOLUTE_X, 3, 4);
      instructionSet[57] = Utils_1.createInstruction(AND_1.default, Utils_1.AddressMode.ABSOLUTE_Y, 3, 4);
      instructionSet[33] = Utils_1.createInstruction(AND_1.default, Utils_1.AddressMode.INDIRECT_X, 2, 6);
      instructionSet[49] = Utils_1.createInstruction(AND_1.default, Utils_1.AddressMode.INDIRECT_Y, 2, 5);
      instructionSet[233] = Utils_1.createInstruction(SBC_1.default, Utils_1.AddressMode.IMMEDIATE, 2, 2);
      instructionSet[229] = Utils_1.createInstruction(SBC_1.default, Utils_1.AddressMode.ZEROPAGE, 2, 3);
      instructionSet[245] = Utils_1.createInstruction(SBC_1.default, Utils_1.AddressMode.ZEROPAGE_X, 2, 4);
      instructionSet[237] = Utils_1.createInstruction(SBC_1.default, Utils_1.AddressMode.ABSOLUTE, 3, 4);
      instructionSet[253] = Utils_1.createInstruction(SBC_1.default, Utils_1.AddressMode.ABSOLUTE_X, 3, 4);
      instructionSet[249] = Utils_1.createInstruction(SBC_1.default, Utils_1.AddressMode.ABSOLUTE_Y, 3, 4);
      instructionSet[225] = Utils_1.createInstruction(SBC_1.default, Utils_1.AddressMode.INDIRECT_X, 2, 6);
      instructionSet[241] = Utils_1.createInstruction(SBC_1.default, Utils_1.AddressMode.INDIRECT_Y, 2, 5);
      instructionSet[10] = Utils_1.createInstruction(ASL_1.default, Utils_1.AddressMode.ACCUMULATOR, 1, 2);
      instructionSet[6] = Utils_1.createInstruction(ASL_1.default, Utils_1.AddressMode.ZEROPAGE, 2, 5);
      instructionSet[22] = Utils_1.createInstruction(ASL_1.default, Utils_1.AddressMode.ZEROPAGE_X, 2, 6);
      instructionSet[14] = Utils_1.createInstruction(ASL_1.default, Utils_1.AddressMode.ABSOLUTE, 3, 6);
      instructionSet[30] = Utils_1.createInstruction(ASL_1.default, Utils_1.AddressMode.ABSOLUTE_X, 3, 7);
      instructionSet[74] = Utils_1.createInstruction(LSR_1.default, Utils_1.AddressMode.ACCUMULATOR, 1, 2);
      instructionSet[70] = Utils_1.createInstruction(LSR_1.default, Utils_1.AddressMode.ZEROPAGE, 2, 5);
      instructionSet[86] = Utils_1.createInstruction(LSR_1.default, Utils_1.AddressMode.ZEROPAGE_X, 2, 6);
      instructionSet[78] = Utils_1.createInstruction(LSR_1.default, Utils_1.AddressMode.ABSOLUTE, 3, 6);
      instructionSet[94] = Utils_1.createInstruction(LSR_1.default, Utils_1.AddressMode.ABSOLUTE_X, 3, 7);
      instructionSet[42] = Utils_1.createInstruction(ROL_1.default, Utils_1.AddressMode.ACCUMULATOR, 1, 2);
      instructionSet[38] = Utils_1.createInstruction(ROL_1.default, Utils_1.AddressMode.ZEROPAGE, 2, 5);
      instructionSet[54] = Utils_1.createInstruction(ROL_1.default, Utils_1.AddressMode.ZEROPAGE_X, 2, 6);
      instructionSet[46] = Utils_1.createInstruction(ROL_1.default, Utils_1.AddressMode.ABSOLUTE, 3, 6);
      instructionSet[62] = Utils_1.createInstruction(ROL_1.default, Utils_1.AddressMode.ABSOLUTE_X, 3, 7);
      instructionSet[106] = Utils_1.createInstruction(ROR_1.default, Utils_1.AddressMode.ACCUMULATOR, 1, 2);
      instructionSet[102] = Utils_1.createInstruction(ROR_1.default, Utils_1.AddressMode.ZEROPAGE, 2, 5);
      instructionSet[118] = Utils_1.createInstruction(ROR_1.default, Utils_1.AddressMode.ZEROPAGE_X, 2, 6);
      instructionSet[110] = Utils_1.createInstruction(ROR_1.default, Utils_1.AddressMode.ABSOLUTE, 3, 6);
      instructionSet[126] = Utils_1.createInstruction(ROR_1.default, Utils_1.AddressMode.ABSOLUTE_X, 3, 7);
      instructionSet[144] = Utils_1.createInstruction(BCC_1.default, Utils_1.AddressMode.RELATIVE, 2, 2);
      instructionSet[176] = Utils_1.createInstruction(BCS_1.default, Utils_1.AddressMode.RELATIVE, 2, 2);
      instructionSet[240] = Utils_1.createInstruction(BEQ_1.default, Utils_1.AddressMode.RELATIVE, 2, 2);
      instructionSet[48] = Utils_1.createInstruction(BMI_1.default, Utils_1.AddressMode.RELATIVE, 2, 2);
      instructionSet[208] = Utils_1.createInstruction(BNE_1.default, Utils_1.AddressMode.RELATIVE, 2, 2);
      instructionSet[16] = Utils_1.createInstruction(BPL_1.default, Utils_1.AddressMode.RELATIVE, 2, 2);
      instructionSet[80] = Utils_1.createInstruction(BVC_1.default, Utils_1.AddressMode.RELATIVE, 2, 2);
      instructionSet[112] = Utils_1.createInstruction(BVS_1.default, Utils_1.AddressMode.RELATIVE, 2, 2);
      instructionSet[36] = Utils_1.createInstruction(BIT_1.default, Utils_1.AddressMode.ZEROPAGE, 2, 3);
      instructionSet[44] = Utils_1.createInstruction(BIT_1.default, Utils_1.AddressMode.ABSOLUTE, 3, 4);
      instructionSet[0] = Utils_1.createInstruction(BRK_1.default, Utils_1.AddressMode.IMPLIED, 0, 7);
      instructionSet[24] = Utils_1.createInstruction(CLC_1.default, Utils_1.AddressMode.IMPLIED, 1, 2);
      instructionSet[216] = Utils_1.createInstruction(CLD_1.default, Utils_1.AddressMode.IMPLIED, 1, 2);
      instructionSet[88] = Utils_1.createInstruction(CLI_1.default, Utils_1.AddressMode.IMPLIED, 1, 2);
      instructionSet[184] = Utils_1.createInstruction(CLV_1.default, Utils_1.AddressMode.IMPLIED, 1, 2);
      instructionSet[56] = Utils_1.createInstruction(SEC_1.default, Utils_1.AddressMode.IMPLIED, 1, 2);
      instructionSet[248] = Utils_1.createInstruction(SED_1.default, Utils_1.AddressMode.IMPLIED, 1, 2);
      instructionSet[120] = Utils_1.createInstruction(SEI_1.default, Utils_1.AddressMode.IMPLIED, 1, 2);
      instructionSet[201] = Utils_1.createInstruction(CMP_1.default, Utils_1.AddressMode.IMMEDIATE, 2, 2);
      instructionSet[197] = Utils_1.createInstruction(CMP_1.default, Utils_1.AddressMode.ZEROPAGE, 2, 3);
      instructionSet[213] = Utils_1.createInstruction(CMP_1.default, Utils_1.AddressMode.ZEROPAGE_X, 2, 4);
      instructionSet[205] = Utils_1.createInstruction(CMP_1.default, Utils_1.AddressMode.ABSOLUTE, 3, 4);
      instructionSet[221] = Utils_1.createInstruction(CMP_1.default, Utils_1.AddressMode.ABSOLUTE_X, 3, 4);
      instructionSet[217] = Utils_1.createInstruction(CMP_1.default, Utils_1.AddressMode.ABSOLUTE_Y, 3, 4);
      instructionSet[193] = Utils_1.createInstruction(CMP_1.default, Utils_1.AddressMode.INDIRECT_X, 2, 6);
      instructionSet[209] = Utils_1.createInstruction(CMP_1.default, Utils_1.AddressMode.INDIRECT_Y, 2, 5);
      instructionSet[224] = Utils_1.createInstruction(CPX_1.default, Utils_1.AddressMode.IMMEDIATE, 2, 2);
      instructionSet[228] = Utils_1.createInstruction(CPX_1.default, Utils_1.AddressMode.ZEROPAGE, 2, 3);
      instructionSet[236] = Utils_1.createInstruction(CPX_1.default, Utils_1.AddressMode.ABSOLUTE, 3, 4);
      instructionSet[192] = Utils_1.createInstruction(CPY_1.default, Utils_1.AddressMode.IMMEDIATE, 2, 2);
      instructionSet[196] = Utils_1.createInstruction(CPY_1.default, Utils_1.AddressMode.ZEROPAGE, 2, 3);
      instructionSet[204] = Utils_1.createInstruction(CPY_1.default, Utils_1.AddressMode.ABSOLUTE, 3, 4);
      instructionSet[198] = Utils_1.createInstruction(DEC_1.default, Utils_1.AddressMode.ZEROPAGE, 2, 5);
      instructionSet[214] = Utils_1.createInstruction(DEC_1.default, Utils_1.AddressMode.ZEROPAGE_X, 2, 6);
      instructionSet[206] = Utils_1.createInstruction(DEC_1.default, Utils_1.AddressMode.ABSOLUTE, 3, 6);
      instructionSet[222] = Utils_1.createInstruction(DEC_1.default, Utils_1.AddressMode.ABSOLUTE_X, 3, 7);
      instructionSet[202] = Utils_1.createInstruction(DEX_1.default, Utils_1.AddressMode.IMPLIED, 1, 2);
      instructionSet[136] = Utils_1.createInstruction(DEY_1.default, Utils_1.AddressMode.IMPLIED, 1, 2);
      instructionSet[230] = Utils_1.createInstruction(INC_1.default, Utils_1.AddressMode.ZEROPAGE, 2, 5);
      instructionSet[246] = Utils_1.createInstruction(INC_1.default, Utils_1.AddressMode.ZEROPAGE_X, 2, 6);
      instructionSet[238] = Utils_1.createInstruction(INC_1.default, Utils_1.AddressMode.ABSOLUTE, 3, 6);
      instructionSet[254] = Utils_1.createInstruction(INC_1.default, Utils_1.AddressMode.ABSOLUTE_X, 3, 7);
      instructionSet[232] = Utils_1.createInstruction(INX_1.default, Utils_1.AddressMode.IMPLIED, 1, 2);
      instructionSet[200] = Utils_1.createInstruction(INY_1.default, Utils_1.AddressMode.IMPLIED, 1, 2);
      instructionSet[73] = Utils_1.createInstruction(EOR_1.default, Utils_1.AddressMode.IMMEDIATE, 2, 2);
      instructionSet[69] = Utils_1.createInstruction(EOR_1.default, Utils_1.AddressMode.ZEROPAGE, 2, 3);
      instructionSet[85] = Utils_1.createInstruction(EOR_1.default, Utils_1.AddressMode.ZEROPAGE_X, 2, 4);
      instructionSet[77] = Utils_1.createInstruction(EOR_1.default, Utils_1.AddressMode.ABSOLUTE, 3, 4);
      instructionSet[93] = Utils_1.createInstruction(EOR_1.default, Utils_1.AddressMode.ABSOLUTE_X, 3, 4);
      instructionSet[89] = Utils_1.createInstruction(EOR_1.default, Utils_1.AddressMode.ABSOLUTE_Y, 3, 4);
      instructionSet[65] = Utils_1.createInstruction(EOR_1.default, Utils_1.AddressMode.INDIRECT_X, 2, 6);
      instructionSet[81] = Utils_1.createInstruction(EOR_1.default, Utils_1.AddressMode.INDIRECT_Y, 2, 5);
      instructionSet[9] = Utils_1.createInstruction(ORA_1.default, Utils_1.AddressMode.IMMEDIATE, 2, 2);
      instructionSet[5] = Utils_1.createInstruction(ORA_1.default, Utils_1.AddressMode.ZEROPAGE, 2, 3);
      instructionSet[21] = Utils_1.createInstruction(ORA_1.default, Utils_1.AddressMode.ZEROPAGE_X, 2, 4);
      instructionSet[13] = Utils_1.createInstruction(ORA_1.default, Utils_1.AddressMode.ABSOLUTE, 3, 4);
      instructionSet[29] = Utils_1.createInstruction(ORA_1.default, Utils_1.AddressMode.ABSOLUTE_X, 3, 4);
      instructionSet[25] = Utils_1.createInstruction(ORA_1.default, Utils_1.AddressMode.ABSOLUTE_Y, 3, 4);
      instructionSet[1] = Utils_1.createInstruction(ORA_1.default, Utils_1.AddressMode.INDIRECT_X, 2, 6);
      instructionSet[17] = Utils_1.createInstruction(ORA_1.default, Utils_1.AddressMode.INDIRECT_Y, 2, 5);
      instructionSet[76] = Utils_1.createInstruction(JMP_1.default, Utils_1.AddressMode.ABSOLUTE, 0, 3);
      instructionSet[108] = Utils_1.createInstruction(JMP_1.default, Utils_1.AddressMode.INDIRECT, 0, 5);
      instructionSet[32] = Utils_1.createInstruction(JSR_1.default, Utils_1.AddressMode.ABSOLUTE, 0, 6);
      instructionSet[64] = Utils_1.createInstruction(RTI_1.default, Utils_1.AddressMode.IMPLIED, 1, 6);
      instructionSet[96] = Utils_1.createInstruction(RTS_1.default, Utils_1.AddressMode.IMPLIED, 1, 6);
      instructionSet[72] = Utils_1.createInstruction(PHA_1.default, Utils_1.AddressMode.IMPLIED, 1, 3);
      instructionSet[8] = Utils_1.createInstruction(PHP_1.default, Utils_1.AddressMode.IMPLIED, 1, 3);
      instructionSet[104] = Utils_1.createInstruction(PLA_1.default, Utils_1.AddressMode.IMPLIED, 1, 4);
      instructionSet[40] = Utils_1.createInstruction(PLP_1.default, Utils_1.AddressMode.IMPLIED, 1, 4);
      instructionSet[169] = Utils_1.createInstruction(LDA_1.default, Utils_1.AddressMode.IMMEDIATE, 2, 2);
      instructionSet[165] = Utils_1.createInstruction(LDA_1.default, Utils_1.AddressMode.ZEROPAGE, 2, 3);
      instructionSet[181] = Utils_1.createInstruction(LDA_1.default, Utils_1.AddressMode.ZEROPAGE_X, 2, 4);
      instructionSet[173] = Utils_1.createInstruction(LDA_1.default, Utils_1.AddressMode.ABSOLUTE, 3, 4);
      instructionSet[189] = Utils_1.createInstruction(LDA_1.default, Utils_1.AddressMode.ABSOLUTE_X, 3, 4);
      instructionSet[185] = Utils_1.createInstruction(LDA_1.default, Utils_1.AddressMode.ABSOLUTE_Y, 3, 4);
      instructionSet[161] = Utils_1.createInstruction(LDA_1.default, Utils_1.AddressMode.INDIRECT_X, 2, 6);
      instructionSet[177] = Utils_1.createInstruction(LDA_1.default, Utils_1.AddressMode.INDIRECT_Y, 2, 5);
      instructionSet[162] = Utils_1.createInstruction(LDX_1.default, Utils_1.AddressMode.IMMEDIATE, 2, 2);
      instructionSet[166] = Utils_1.createInstruction(LDX_1.default, Utils_1.AddressMode.ZEROPAGE, 2, 3);
      instructionSet[182] = Utils_1.createInstruction(LDX_1.default, Utils_1.AddressMode.ZEROPAGE_Y, 2, 4);
      instructionSet[174] = Utils_1.createInstruction(LDX_1.default, Utils_1.AddressMode.ABSOLUTE, 3, 4);
      instructionSet[190] = Utils_1.createInstruction(LDX_1.default, Utils_1.AddressMode.ABSOLUTE_Y, 3, 4);
      instructionSet[160] = Utils_1.createInstruction(LDY_1.default, Utils_1.AddressMode.IMMEDIATE, 2, 2);
      instructionSet[164] = Utils_1.createInstruction(LDY_1.default, Utils_1.AddressMode.ZEROPAGE, 2, 3);
      instructionSet[180] = Utils_1.createInstruction(LDY_1.default, Utils_1.AddressMode.ZEROPAGE_X, 2, 4);
      instructionSet[172] = Utils_1.createInstruction(LDY_1.default, Utils_1.AddressMode.ABSOLUTE, 3, 4);
      instructionSet[188] = Utils_1.createInstruction(LDY_1.default, Utils_1.AddressMode.ABSOLUTE_X, 3, 4);
      instructionSet[133] = Utils_1.createInstruction(STA_1.default, Utils_1.AddressMode.ZEROPAGE, 2, 3);
      instructionSet[149] = Utils_1.createInstruction(STA_1.default, Utils_1.AddressMode.ZEROPAGE_X, 2, 4);
      instructionSet[141] = Utils_1.createInstruction(STA_1.default, Utils_1.AddressMode.ABSOLUTE, 3, 4);
      instructionSet[157] = Utils_1.createInstruction(STA_1.default, Utils_1.AddressMode.ABSOLUTE_X, 3, 5);
      instructionSet[153] = Utils_1.createInstruction(STA_1.default, Utils_1.AddressMode.ABSOLUTE_Y, 3, 5);
      instructionSet[129] = Utils_1.createInstruction(STA_1.default, Utils_1.AddressMode.INDIRECT_X, 2, 6);
      instructionSet[145] = Utils_1.createInstruction(STA_1.default, Utils_1.AddressMode.INDIRECT_Y, 2, 6);
      instructionSet[134] = Utils_1.createInstruction(STX_1.default, Utils_1.AddressMode.ZEROPAGE, 2, 3);
      instructionSet[150] = Utils_1.createInstruction(STX_1.default, Utils_1.AddressMode.ZEROPAGE_Y, 2, 4);
      instructionSet[142] = Utils_1.createInstruction(STX_1.default, Utils_1.AddressMode.ABSOLUTE, 3, 4);
      instructionSet[132] = Utils_1.createInstruction(STY_1.default, Utils_1.AddressMode.ZEROPAGE, 2, 3);
      instructionSet[148] = Utils_1.createInstruction(STY_1.default, Utils_1.AddressMode.ZEROPAGE_X, 2, 4);
      instructionSet[140] = Utils_1.createInstruction(STY_1.default, Utils_1.AddressMode.ABSOLUTE, 3, 4);
      instructionSet[234] = Utils_1.createInstruction(NOP_1.default, Utils_1.AddressMode.IMPLIED, 1, 2);
      instructionSet[170] = Utils_1.createInstruction(TAX_1.default, Utils_1.AddressMode.IMPLIED, 1, 2);
      instructionSet[168] = Utils_1.createInstruction(TAY_1.default, Utils_1.AddressMode.IMPLIED, 1, 2);
      instructionSet[186] = Utils_1.createInstruction(TSX_1.default, Utils_1.AddressMode.IMPLIED, 1, 2);
      instructionSet[138] = Utils_1.createInstruction(TXA_1.default, Utils_1.AddressMode.IMPLIED, 1, 2);
      instructionSet[154] = Utils_1.createInstruction(TXS_1.default, Utils_1.AddressMode.IMPLIED, 1, 2);
      instructionSet[152] = Utils_1.createInstruction(TYA_1.default, Utils_1.AddressMode.IMPLIED, 1, 2);
      exports.default = instructionSet;
    }
  });

  // mat-sz/6502/lib/index.js
  var require_lib = __commonJS({
    "mat-sz/6502/lib/index.js"(exports) {
      "use strict";
      Object.defineProperty(exports, "__esModule", { value: true });
      var instructionSet_1 = require_instructionSet();
      var Utils_1 = require_Utils();
      exports.MEMORY_SIZE = 65536;
      var State = (
        /** @class */
        /* @__PURE__ */ (function() {
          function State2() {
            this.PC = 0;
            this.SP = 0;
            this.A = 0;
            this.X = 0;
            this.Y = 0;
            this.NF = false;
            this.VF = false;
            this.DF = false;
            this.IF = true;
            this.ZF = false;
            this.CF = false;
            this.NMI = false;
            this.IRQ = false;
            this.cycles = 0;
          }
          return State2;
        })()
      );
      exports.State = State;
      exports.step = function(state, getMemory, setMemory) {
        state.cycles = 0;
        var code = getMemory(state.PC);
        if (code in instructionSet_1.default) {
          state = instructionSet_1.default[code].fn(state, getMemory, setMemory);
        } else {
          throw new Error("Unsupported opcode. " + code.toString(16) + " at " + state.PC.toString(16));
        }
        if (state.NMI) {
          exports.performIRQ(state, getMemory, setMemory, 65530);
          state.NMI = false;
        } else if (!state.IF && state.IRQ) {
          exports.performIRQ(state, getMemory, setMemory, 65534);
          state.IRQ = false;
        }
        return state;
      };
      exports.performIRQ = function(state, getMemory, setMemory, offset, brk, push) {
        if (brk === void 0) {
          brk = false;
        }
        if (push === void 0) {
          push = true;
        }
        if (push) {
          Utils_1.pushWord(state, setMemory, state.PC);
          Utils_1.pushByte(state, setMemory, Utils_1.getSR(state, brk));
        }
        state.IF = true;
        state.PC = Utils_1.getWord(state, getMemory, offset);
        return state;
      };
      exports.performReset = function(getMemory) {
        var state = exports.performIRQ(new State(), getMemory, function(_) {
          return 0;
        }, 65532, false, false);
        state.SP = 253;
        return state;
      };
    }
  });

  // bundle6502.mjs
  var bundle6502_exports = {};
  __reExport(bundle6502_exports, __toESM(require_lib(), 1));
  return __toCommonJS(bundle6502_exports);
})();
