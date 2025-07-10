#ifndef WARDUINO_PRIMITIVES_MACROS_H
#define WARDUINO_PRIMITIVES_MACROS_H

// Primitive function signature macros
#define def_prim(function_name, type) void prim_##function_name()
#define def_prim_reverse(function_name) void reverse_##function_name()
#define def_prim_serialize(function_name) void serialize_##function_name()

// Signature typedefs or enums (adjust as needed)
#define NoneToNoneU32 0
#define NoneToOneU32 1
#define NoneToOneU64 2
#define oneToNoneU32 3
#define oneToOneU32 4
#define oneToOneI32 5
#define twoToNoneU32 6
#define twoToOneU32 7
#define threeToNoneU32 8
#define fourToNoneU32 9
#define fourToOneU32 10
#define tenToOneU32 11

// Argument access macros (adjust based on your call convention)
#define arg0 args[0]
#define pop_args(n) /* TODO: pop n args from the stack */

#endif // WARDUINO_PRIMITIVES_MACROS_H


#ifndef WARDUINO_PRIM_H
#define WARDUINO_PRIM_H

#include "../Utils/macros.h"
#include "../WARDuino.h"

/**
 * Find a primitive function by looking it up
 *
 * @param symbol name of primitive function
 * @param val    location to store a pointer to the function
 * @return true if function is found and assigned to val
 */
bool resolve_primitive(char *symbol, Primitive *val);

/**
 * Handle import of memory by keeping a array of 256 pages.
 * If more imports of memory are needed, this should be replaced by a
 * nicer function that allows you to specify the different kinds of
 * memory that mey be needed
 *
 * @param symbol name
 * @param val    location to store memory to
 * @return true if memory is found and assigned to val
 */
bool resolve_external_memory(char *symbol, Memory **val);

void install_primitives();

std::vector<IOStateElement *> get_io_state(Module *m);

void restore_external_state(Module *m,
                            const std::vector<IOStateElement> &external_state);

inline void create_stack(std::vector<StackValue> *) {}

template <typename T, typename... Ts>
void create_stack(std::vector<StackValue> *stack, T value, Ts... args) {
    StackValue stackValue;
    if constexpr (std::is_same<T, int32_t>() || std::is_same<T, int>()) {
        stackValue.value.int32 = value;
        stackValue.value_type = I32;
    } else if constexpr (std::is_same<T, uint32_t>()) {
        stackValue.value.uint32 = value;
        stackValue.value_type = I32;
    } else if constexpr (std::is_same<T, int64_t>()) {
        stackValue.value.int64 = value;
        stackValue.value_type = I64;
    } else if constexpr (std::is_same<T, uint64_t>()) {
        stackValue.value.uint64 = value;
        stackValue.value_type = I64;
    } else if constexpr (std::is_same<T, float>()) {
        stackValue.value.f32 = value;
        stackValue.value_type = F32;
    } else if constexpr (std::is_same<T, double>()) {
        stackValue.value.f64 = value;
        stackValue.value_type = F64;
    } else {
        // This will trigger a compile time error if a different unsupported
        // type is used.
        static_assert(
            sizeof(T) == 0,
            "Unsupported argument type! Expected i32, i64, f32 or f64.");
    }
    stack->push_back(stackValue);

    create_stack(stack, args...);
}

template <typename... Ts>
void invoke_primitive(Module *m, const std::string &function_name, Ts... args) {
    Primitive primitive;
    resolve_primitive((char *)function_name.c_str(), &primitive);

    std::vector<StackValue> argStack;
    create_stack(&argStack, args...);

    for (auto arg : argStack) {
        m->stack[++m->sp] = arg;
    }
    primitive(m);
}

#endif
