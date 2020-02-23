/**
 * Simple SMA16 VM in C. 
 */
#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <unistd.h>
#include <termios.h>

#ifndef DISABLE_TIMING
#define ENABLE_TIMING
#endif

#ifndef DISABLE_DEBUG
#define ENABLE_DEBUG
#endif

#ifndef DISABLE_SIGINT
#define ENABLE_SIGINT
#endif

#ifdef ENABLE_TIMING
#include <time.h>
#endif

#ifdef ENABLE_SIGINT
#include <signal.h>
#endif

#ifdef MEMORY_FILE
const char *usage_line = "Usage: sma16vm [options]";
#else
const char *usage_line = "Usage: sma16vm [options] input_memory_file";
#endif

const char *version_string = "sma16 v0.1";

const char *options_string = "Options:\n"
                             "  --version\tDisplay version.\n"
                             "  --help\tDisplay this message.\n"
#ifdef ENABLE_DEBUG
                             "  --debug\tDisplay debug information.\n"
#endif
#ifdef ENABLE_TIMING
                             "  --time\tDisplay timing information\n"
#endif
                             "\n"
                             "Short forms can also be used as per usual.";

// Workaround for missing defines
#define CLOCK_PROCESS_CPUTIME_ID 2
#define SIGINT 2

#define UPPER(x) (x & 0xf000)
#define INST(x) ((x >> 12) & 0xf)
#define DATA(x) (x & 0xfff)
#define PRESERVE_INST 0x1
#define SHIFT_INST 0x0
#define SHIFT(val, preserve_inst) ((val << 1) | (preserve_inst & 0x1))
#define NEXT_ 0xffff

#define ASCII_OUT 0x00A
#define SMALL_OUT 0x00B
#define TERM_CONF 0x00C
#define MEMORY_CONF 0x00D

#define RESET_VECTOR 0x000
#define FAULT_VECTOR 0x001
#define SOFTWARE_VECTOR 0x002

#define INTER_REASON 0x008

enum InterruptReason
{
    IR_UNKNOWN = 0x0000,
    IR_UNSUPPORTED = 0x0ff0,
};

#define INTER_RETURN 0x009

#define MEM(A, I, D) \
    {                \
        (A & 0xffff), (((I & 0x000f) << 12) | (D & 0x0fff))},

#define MBP(A, X, Y) \
    {                \
        (A & 0xffff), (((X & 0x00ff) << 8) | (Y & 0x00ff))},

#define DEBUG(X) \
    if (debug)   \
    puts(X)

#define START_PROGRAM const __prog_elem PROGRAM[] = {
#define END_PROGRAM \
    }               \
    ;

#define CHP(x, y) ((CHP_P(x) << 6) | CHP_P(y))
#define CHP_P(x) (CHP_P_##x)
#define CHP_P_A 0
#define CHP_P_B 1
#define CHP_P_C 2
#define CHP_P_D 3
#define CHP_P_E 4
#define CHP_P_F 5
#define CHP_P_G 6
#define CHP_P_H 7
#define CHP_P_I 8
#define CHP_P_J 9
#define CHP_P_K 10
#define CHP_P_L 11
#define CHP_P_M 12
#define CHP_P_N 13
#define CHP_P_O 14
#define CHP_P_P 15
#define CHP_P_Q 16
#define CHP_P_R 17
#define CHP_P_S 18
#define CHP_P_T 19
#define CHP_P_U 20
#define CHP_P_V 21
#define CHP_P_W 22
#define CHP_P_X 23
#define CHP_P_Y 24
#define CHP_P_Z 25
#define CHP_P_a 26
#define CHP_P_b 27
#define CHP_P_c 28
#define CHP_P_d 29
#define CHP_P_e 30
#define CHP_P_f 31
#define CHP_P_g 32
#define CHP_P_h 33
#define CHP_P_i 34
#define CHP_P_j 35
#define CHP_P_k 36
#define CHP_P_l 37
#define CHP_P_m 38
#define CHP_P_n 39
#define CHP_P_o 40
#define CHP_P_p 41
#define CHP_P_q 42
#define CHP_P_r 43
#define CHP_P_s 44
#define CHP_P_t 45
#define CHP_P_u 46
#define CHP_P_v 47
#define CHP_P_w 48
#define CHP_P_x 49
#define CHP_P_y 50
#define CHP_P_z 51
#define CHP_P_0 52
#define CHP_P_1 53
#define CHP_P_2 54
#define CHP_P_3 55
#define CHP_P_4 56
#define CHP_P_5 57
#define CHP_P_6 58
#define CHP_P_7 59
#define CHP_P_8 60
#define CHP_P_9 61
#define CHP_P_ CHP_P_SPACE
#define CHP_P_SPACE 62
#define CHP_P__ CHP_P_NONE
#define CHP_P_NONE 63

const char *HALT_STRING = "HALT";

typedef struct
{
    uint16_t address;
    uint16_t data;
} __prog_elem;

enum Instructions
{
    HALT = 0x0,
    /* 0x1 */
    JUMP = 0x2,
    JUMPZ = 0x3,
    LOAD = 0x4,
    STORE = 0x5,
    LSHFT = 0x6,
    RSHFT = 0x7,
    XOR = 0x8,
    AND = 0x9,
    SFULL = 0xA,
    ADD = 0xB,
    /* 0xC */
    POP = 0xD,
    PUSH = 0xE,
    NOOP = 0xF
};

__attribute__((always_inline)) static inline char transform_char(uint16_t x)
{
    if (x >= 0 && x < 26)
        return x + 'A';
    if (x >= 26 && x < 52)
        return x - 26 + 'a';
    if (x >= 52 && x < 62)
        return x - 52 + '0';
    if (x == 62)
        return ' ';
    return '\0';
}

static inline char get_single_char()
{
    static struct termios old_settings, new_settings;
    tcgetattr(STDIN_FILENO, &old_settings);
    new_settings = old_settings;
    new_settings.c_lflag &= ~(ICANON | ECHO);
    tcsetattr(STDIN_FILENO, TCSANOW, &new_settings);
    const char result = getchar();
    tcsetattr(STDIN_FILENO, TCSANOW, &old_settings);
    return result;
}

#ifdef ENABLE_SIGINT
static bool sigint_halt_flag = false;

void handle_sigint(int sig)
{
    sigint_halt_flag = true;
}
#endif

#ifdef MEMORY_FILE
#include "memory_file.s16"
#endif

int main(int argc, char *argv[])
{
#ifdef ENABLE_SIGINT
    // Register signal handler
    signal(SIGINT, handle_sigint);
#endif

    // Flags
#ifdef ENABLE_DEBUG
    bool debug = false;
#endif
#ifdef ENABLE_TIMING
    bool timed = false;
#endif
#ifndef MEMORY_FILE
    int input_file_index = 0;
#endif
    bool help = false;
    bool version = false;

    // CPU State
    uint16_t memory[4096] = {0};
    bool halt = false;
    bool test = false;
    uint16_t accumulator = 0;
    uint16_t program_counter = 0;

#ifdef ENABLE_TIMING
    // Timing
    struct timespec start;
    struct timespec end;
#endif

    for (int arg = 0; arg < argc; arg++)
    {
        if (argv[arg][0] == '-')
        {
            if (strncmp(argv[arg], "-h", 3) == 0 || strncmp(argv[arg], "--help", 7) == 0)
                help = true;
            else if (strncmp(argv[arg], "-v", 3) == 0 || strncmp(argv[arg], "--version", 10) == 0)
                version = true;
#ifdef ENABLE_DEBUG
            else if (strncmp(argv[arg], "-d", 3) == 0 || strncmp(argv[arg], "--debug", 8) == 0)
                debug = true;
#endif
#ifdef ENABLE_TIMING
            else if (strncmp(argv[arg], "-t", 3) == 0 || strncmp(argv[arg], "--timed", 8) == 0)
                timed = true;
#endif
        }
#ifndef MEMORY_FILE
        else if (arg != 0)
        {
            input_file_index = arg;
        }
#endif
    }

    if (version)
    {
        puts(version_string);
        return 0;
    }

    if (help)
    {
        puts(usage_line);
        puts(options_string);
        return 0;
    }

#ifdef MEMORY_FILE
    /* Load program */
    uint16_t last_address = 0;
    for (uint16_t index = 0; index < (sizeof(PROGRAM) / sizeof(__prog_elem)); index++)
    {
        uint16_t address = PROGRAM[index].address;
        if (address == NEXT_)
        {
            address = (last_address + 1) & 0x0FFF;
        }
        address = address & 0x0fff;
        memory[address] = PROGRAM[index].data;
        last_address = address;
    }
#else
    if (input_file_index == 0)
    {
        fputs("No input file.", stderr);
        return 1;
    }
    else
    {
        FILE *input_file = fopen(argv[input_file_index], "r");

        if (NULL == input_file)
        {
            fputs("Could not open file.", stderr);
            return 2;
        }

        const size_t read_bytes = fread((uint8_t *)memory, 1, 8192, input_file);

        if (read_bytes % 2 != 0)
        {
            fputs("Warning, uneven number of bytes read from memory image.", stderr);
        }

        for (size_t word_index = 0; word_index < read_bytes / 2; word_index++)
        {
            memory[word_index] = ((memory[word_index] & 0xff) << 8) | ((memory[word_index] >> 8) & 0xff);
        }

        if (0 != fclose(input_file))
        {
            fputs("Failed to close file.", stderr);
            return 3;
        }
    }
#endif

    for (;;)
    {
#ifdef ENABLE_DEBUG
        if (debug)
        {
            puts("+---------+-----+-------+--- -- -- - - -");
            puts("| [ ACC ] | PC  | PROG  | -> OUTPUT");
            puts("+---------+-----+-------+--- -- -- - - -");
        }
#endif
#ifdef ENABLE_TIMING
        if (timed)
            clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &start);
#endif
        while (!halt)
        {
#ifdef ENABLE_DEBUG
            if (debug)
                printf("| [%01x:%03x] | %03x | %01x:%03x | -> ", INST(accumulator), DATA(accumulator), program_counter, INST(memory[program_counter]), DATA(memory[program_counter]));
#endif
            switch (INST(memory[program_counter]))
            {
            case HALT:
            {
#ifdef ENABLE_DEBUG
                if (debug)
                    fputs(HALT_STRING, stdout); // Avoid newline
                else
#endif
                    puts(HALT_STRING);
                halt = true;
                program_counter++;
            }
            break;
            case JUMP:
            {
                program_counter = DATA(memory[program_counter]);
            }
            break;
            case JUMPZ:
            {
                if (test)
                    program_counter = DATA(memory[program_counter]);
                else
                    program_counter++;
            }
            break;
            case LOAD:
            {
                accumulator = memory[DATA(memory[program_counter])];
                program_counter++;
            }
            break;
            case STORE:
            {
                const uint16_t address = DATA(memory[program_counter]);
                if (address == SMALL_OUT)
                {
                    const uint16_t first_char = 0x003F & (accumulator >> 6);
                    const uint16_t second_char = 0x003F & accumulator;
                    if (first_char != '\0')
                        putc(transform_char(first_char), stdout);
                    if (second_char != '\0')
                        putc(transform_char(second_char), stdout);
                }
                else if (address == ASCII_OUT)
                {
                    const char to_print = accumulator & 0x00ff;
#ifdef ENABLE_DEBUG
                    if (debug && to_print == '\n')
                    {
                        putc('\\', stdout);
                        putc('n', stdout);
                    }
                    else
                    {
#endif
                        putc(to_print, stdout);
#ifdef ENABLE_DEBUG
                    }
#endif
                }
                memory[address] = UPPER(memory[address]) | DATA(accumulator);
                program_counter++;
            }
            break;
            case SFULL:
            {
                const uint16_t address = DATA(memory[program_counter]);
                if (address == SMALL_OUT)
                {
                    const uint16_t first_char = 0x003F & (accumulator >> 6);
                    const uint16_t second_char = 0x003F & accumulator;
                    if (first_char != '\0')
                        putc(transform_char(first_char), stdout);
                    if (second_char != '\0')
                        putc(transform_char(second_char), stdout);
                }
                else if (address == ASCII_OUT)
                {
                    putc(accumulator & 0x00ff, stdout);
                }
                memory[address] = accumulator;
                program_counter++;
            }
            break;
            case LSHFT:
            {
                const uint16_t shift = DATA(memory[program_counter]);
                const uint16_t inst = UPPER(accumulator);
                if (shift & 0x1)
                    accumulator = accumulator & 0x0fff;
                accumulator = accumulator << (shift >> 1);
                if (shift & 0x1)
                    accumulator = (accumulator & 0xfff) | inst;
                program_counter++;
            }
            break;
            case RSHFT:
            {
                const uint16_t shift = DATA(memory[program_counter]);
                const uint16_t inst = UPPER(accumulator);
                if (shift & 0x1)
                    accumulator = accumulator & 0x0fff;
                accumulator = accumulator >> (shift >> 1);
                if (shift & 0x1)
                    accumulator = (accumulator & 0xfff) | inst;
                program_counter++;
            }
            break;
            case XOR:
            {
                accumulator ^= DATA(memory[program_counter]);
                program_counter++;
            }
            break;
            case AND:
            {
                accumulator &= DATA(memory[program_counter]) | 0xf000;
                program_counter++;
            }
            break;
            case ADD:
            {
                const uint16_t inst = UPPER(accumulator);
                accumulator = inst | ((DATA(accumulator) + DATA(memory[program_counter])) & 0xfff);
                test = accumulator == 0;
                program_counter++;
            }
            break;
            case POP:
            {
                memory[INTER_RETURN] = program_counter + 1;
                program_counter = FAULT_VECTOR;
                memory[INTER_REASON] = IR_UNSUPPORTED + POP;
            }
            break;
            case PUSH:
            {
                memory[INTER_RETURN] = program_counter + 1;
                program_counter = FAULT_VECTOR;
                memory[INTER_REASON] = IR_UNSUPPORTED + PUSH;
            }
            break;
            case NOOP:
            default:
            {
                program_counter++;
            }
            break;
            }

#ifdef ENABLE_SIGINT
            if (sigint_halt_flag)
            {
                halt = true;
                sigint_halt_flag = false;
#ifdef ENABLE_DEBUG
                if (debug)
                    fputs(" USER HALT", stdout);
                else
#endif
                    puts(" USER HALT");
            }
#endif
#ifdef ENABLE_DEBUG
            if (debug)
                putc('\n', stdout);
#endif
        }
#ifdef ENABLE_TIMING
        if (timed)
            clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &end);
#endif
#ifdef ENABLE_DEBUG
        if (debug)
            puts("+---------+-----+-------+--- -- -- - - -");
#endif

        if (isatty(STDIN_FILENO) && isatty(STDOUT_FILENO))
        {
#ifdef ENABLE_TIMING
            if (timed)
                printf("System halted after %ldus.", (end.tv_sec - start.tv_sec) * 1000000 + (end.tv_nsec - start.tv_nsec) / 1000);
            else
#endif
                fputs("System halted.", stdout);
            puts(" Press C to continue, or any other key to exit.");

            const char input = get_single_char();

            if (input == 'C' || input == 'c')
            {
                halt = false;
            }
            else
            {
                break;
            }
        }
        else
        {
            puts("System halted.");
            break;
        }
    }

    return 0;
}
