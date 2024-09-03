#include "mem.h"

#include <cstdlib>
#include <cstring>

#include "../Utils/macros.h"

#ifdef ARDUINO
#include "Arduino.h"
#endif

#ifdef __CHERI_PURE_CAPABILITY__
#include <cheriintrin.h>
#endif

// Assert calloc
void *acalloc(size_t nmemb, size_t size, const char *name, bool psram) {
    if ((int)(nmemb * size) == 0) {
        return nullptr;
    } else {
        debug("IN Acalloc count: %zu, size: %zu for %s \n", nmemb, size, name);
#ifdef ARDUINO
        void *res;
        if (psramInit() && psram) {
            res = ps_calloc(nmemb, size);
        } else {
            res = calloc(nmemb, size);
        }
#else
        void *res = calloc(nmemb, size);
#endif
        debug("Done ... Acalloc\n");
        if (res == nullptr) {
            debug("FAILED ... Acalloc\n");
            FATAL("Could not allocate %d bytes for %s \n", (int)(nmemb * size),
                  name);
        }
        debug("NOT FAILED ... Acalloc\n");
#if defined(__CHERI_PURE_CAPABILITY__)
	// CHERI hardware bounds checking enabled
	res = cheri_bounds_set(res, nmemb*size);
#endif
        return res;
    }
}

// Assert realloc/calloc
void *arecalloc(void *ptr, size_t old_nmemb, size_t nmemb, size_t size,
                const char *name, bool psram) {
#ifdef ARDUINO
    void *res;
    if (psramInit() && psram) {
        res = (size_t *)ps_calloc(nmemb, size);
    } else {
        res = (size_t *)calloc(nmemb, size);
    }
#else
    auto *res = (size_t *)calloc(nmemb, size);
#endif
    if (res == nullptr) {
        FATAL("Could not allocate %d bytes for %s", (int)(nmemb * size), name);
    }
    memset(res, 0, nmemb * size);  // initialize memory with 0
    memmove(res, ptr, old_nmemb * size);
    free(ptr);
    return res;
}
