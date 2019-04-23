/* 
 __      __                  .___    .__               
/  \    /  \_____ _______  __| _/_ __|__| ____   ____  
\   \/\/   /\__  \\_  __ \/ __ |  |  \  |/    \ /  _ \ 
 \        /  / __ \|  | \/ /_/ |  |  /  |   |  (  <_> )
  \__/\  /  (____  /__|  \____ |____/|__|___|  /\____/ 
       \/        \/           \/             \/        

WARDuino (c) by Christophe Scholliers & Robbert Gurdeep Singh 

WARDuino is licensed under a
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-nc-sa/4.0/>.
*/

/**
 * This file lists the primitives of the language and stores them in the
 * primitives
 * 
 * Adding a primitive:
 *  1) Bump up the NUM_PRIMITIVES constant
 *  2) Define <primitive>_type 
 *  3) Define a function void primitive(Module* m)
 *  4) Extend the install_primitives function 
 * 
 */
#include "primitives.h"

extern "C" {
  #include "debug.h"
  #include "util.h"
  #include "debug.h"
}

#ifdef ARDUINO
#include "Arduino.h"

#else
#include <chrono>
#include <thread>
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define NUM_PRIMITIVES 2
#ifdef ARDUINO
  #define NUM_PRIMITIVES_ARDUINO 4
#else
  #define NUM_PRIMITIVES_ARDUINO 3
#endif 

#define ALL_PRIMITIVES  NUM_PRIMITIVES + NUM_PRIMITIVES_ARDUINO

// Global index for installing primitives
int prim_index = 0;

/*
    Private macros to install a primitive
*/
#define install_primitive(prim_name)        \
  {    \
    dbg_info("installing primitive number: %d  of %d with name: %s\n",prim_index,ALL_PRIMITIVES,#prim_name);\
    if( prim_index < ALL_PRIMITIVES ) {                                      \
      PrimitiveEntry* p = &primitives[prim_index++]; \
      p->name = #prim_name;             \
      p->f = &prim_name;                 \
    } else {\
        FATAL("pim_index out of bounds");\
    }\
  }\


#define def_prim(function_name,type)  \
  Type function_name ## _type = type; \
  void function_name(Module* m)   


// TODO: use fp
#define pop_args(n) m->sp -= n
#define get_arg(m,arg) m->stack[m->sp-arg].value
#define arg0 get_arg(m,0)
#define arg1 get_arg(m,1)
#define arg2 get_arg(m,2)
#define arg3 get_arg(m,2)
#define arg4 get_arg(m,2)


// The primitive table
PrimitiveEntry primitives[ALL_PRIMITIVES];

//------------------------------------------------------
// Primitive Blink
//------------------------------------------------------
Type nullType;

def_prim(blink, nullType) 
{
  size_t cnt = arg0.uint32;
  for (size_t i = 1; i < cnt; i++)
  {
    printf("BLINK %lu/%lu!\n", i, cnt);
  }
  pop_args(1);
}

//------------------------------------------------------
// Primitive Flash
//------------------------------------------------------

def_prim(flash, nullType)
{
  size_t cnt = arg0.uint32;
  for (size_t i = cnt; i > 0; i--)
  {
    printf("FLASH %lu/%lu!\n", i, cnt);
  }
  pop_args(1);
}


//------------------------------------------------------
// Arduino Specific Functions
//------------------------------------------------------

#ifdef ARDUINO
def_prim(chip_pin_mode,nullType) {   
  printf("chip_pin_mode \n");

  uint8_t pin  = arg1.uint32;
  uint8_t mode = arg0.uint32;

  pinMode(pin, mode);

  pop_args(2);

}

def_prim(chip_digital_write, nullType) {
  printf("chip_digital_write \n");
  uint8_t pin = arg1.uint32;
  uint8_t val = arg0.uint32;
  digitalWrite(pin, val);
  pop_args(2);
}

def_prim(chip_delay, nullType){ 
  printf("chip_delay \n");
  delay(arg0.uint32);
  pop_args(1);
}

def_prim(chip_digital_read, nullType) {
  uint8_t pin = arg0.uint32;
  pop_args(1);
  //pushInt32(digitalRead(pin));
}

#else

def_prim(chip_pin_mode,nullType) {   
  dbg_trace("EMU: chip_pin_mode(%u,%u) \n",arg1.uint32,arg0.uint32);
  pop_args(2);
}

def_prim(chip_digital_write, nullType) {
  dbg_trace("EMU: chip_digital_write(%u,%u) \n",arg1.uint32,arg0.uint32);
  pop_args(2);
}

def_prim(chip_delay, nullType){ 
  using namespace std::this_thread; // sleep_for, sleep_until
  using namespace std::chrono; // nanoseconds, system_clock, seconds
  dbg_trace("EMU: chip_delay(%u) \n",arg0.uint32);
  sleep_for(milliseconds(arg0.uint32));
  dbg_trace("EMU: .. done\n");
  pop_args(1);
}

#endif

/* 
int analogRead(uint8_t pin)
void analogReference(uint8_t mode)
void analogWrite(uint8_t pin, int val)
void analogWriteFreq(uint32_t freq)
void analogWriteRange(uint32_t range)
*/


//------------------------------------------------------
// Installing all the primitives
//------------------------------------------------------
void install_primitives(void)
{
  dbg_info("INSTALLING PRIMITIVES\n");
  install_primitive(blink);
  install_primitive(flash);
  install_primitive(chip_pin_mode);
  install_primitive(chip_digital_write);
  install_primitive(chip_delay);

  #ifdef ARDUINO
      dbg_info("INSTALLING ARDUINO\n");
      install_primitive(chip_digital_read);
  #endif 
}

//------------------------------------------------------
// resolving the primitives
//------------------------------------------------------
bool resolve_primitive(char *symbol, Primitive *val)
{
  for (size_t i = 0; i < ALL_PRIMITIVES; i++)
  {
    if (!strcmp(symbol, primitives[i].name))
    {
      *val = primitives[i].f;
      return true;
    }
  }
  FATAL( "Could not find primitive %s \n" , symbol);
  return false;
}