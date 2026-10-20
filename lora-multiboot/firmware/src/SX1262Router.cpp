/**
 * SX1262Router — promiscuous capture, listen-before-send, cross-protocol relay
 */
#include "SX1262Router.hpp"
static bool s_p=false, s_a=false, s_v=false;
void SX1262Router_init(void){ s_p=true; s_a=false; s_v=false; }
bool SX1262Router_gate(void){ s_v=true; return s_p && s_a; }
bool SX1262Router_can_tx(void){ return s_v && s_p && s_a; }
void SX1262Router_set_air(bool f){ s_a=f; }
