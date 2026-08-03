#define SOUFFLE_GENERATOR_VERSION "2.5"
#include "souffle/CompiledSouffle.h"
#include "souffle/SignalHandler.h"
#include "souffle/SouffleInterface.h"
#include "souffle/datastructure/BTree.h"
#include "souffle/datastructure/Nullaries.h"
#include "souffle/io/IOSystem.h"
#include "souffle/utility/MiscUtil.h"
#include <any>
namespace functors {
extern "C" {
}
} //namespace functors
namespace souffle::t_btree_000_ii__0_1__11__10 {
using namespace souffle;
struct Type {
static constexpr Relation::arity_type Arity = 2;
using t_tuple = Tuple<RamDomain, 2>;
struct t_comparator_0{
 int operator()(const t_tuple& a, const t_tuple& b) const {
  return (ramBitCast<RamSigned>(a[0]) < ramBitCast<RamSigned>(b[0])) ? -1 : (ramBitCast<RamSigned>(a[0]) > ramBitCast<RamSigned>(b[0])) ? 1 :((ramBitCast<RamSigned>(a[1]) < ramBitCast<RamSigned>(b[1])) ? -1 : (ramBitCast<RamSigned>(a[1]) > ramBitCast<RamSigned>(b[1])) ? 1 :(0));
 }
bool less(const t_tuple& a, const t_tuple& b) const {
  return (ramBitCast<RamSigned>(a[0]) < ramBitCast<RamSigned>(b[0]))|| ((ramBitCast<RamSigned>(a[0]) == ramBitCast<RamSigned>(b[0])) && ((ramBitCast<RamSigned>(a[1]) < ramBitCast<RamSigned>(b[1]))));
 }
bool equal(const t_tuple& a, const t_tuple& b) const {
return (ramBitCast<RamSigned>(a[0]) == ramBitCast<RamSigned>(b[0]))&&(ramBitCast<RamSigned>(a[1]) == ramBitCast<RamSigned>(b[1]));
 }
};
using t_ind_0 = btree_set<t_tuple,t_comparator_0>;
t_ind_0 ind_0;
using iterator = t_ind_0::iterator;
struct context {
t_ind_0::operation_hints hints_0_lower;
t_ind_0::operation_hints hints_0_upper;
};
context createContext() { return context(); }
bool insert(const t_tuple& t);
bool insert(const t_tuple& t, context& h);
bool insert(const RamDomain* ramDomain);
bool insert(RamDomain a0,RamDomain a1);
bool contains(const t_tuple& t, context& h) const;
bool contains(const t_tuple& t) const;
std::size_t size() const;
iterator find(const t_tuple& t, context& h) const;
iterator find(const t_tuple& t) const;
range<iterator> lowerUpperRange_00(const t_tuple& /* lower */, const t_tuple& /* upper */, context& /* h */) const;
range<iterator> lowerUpperRange_00(const t_tuple& /* lower */, const t_tuple& /* upper */) const;
range<t_ind_0::iterator> lowerUpperRange_11(const t_tuple& lower, const t_tuple& upper, context& h) const;
range<t_ind_0::iterator> lowerUpperRange_11(const t_tuple& lower, const t_tuple& upper) const;
range<t_ind_0::iterator> lowerUpperRange_10(const t_tuple& lower, const t_tuple& upper, context& h) const;
range<t_ind_0::iterator> lowerUpperRange_10(const t_tuple& lower, const t_tuple& upper) const;
bool empty() const;
std::vector<range<iterator>> partition() const;
void purge();
iterator begin() const;
iterator end() const;
void printStatistics(std::ostream& o) const;
};
} // namespace souffle::t_btree_000_ii__0_1__11__10 
namespace souffle::t_btree_000_ii__0_1__11__10 {
using namespace souffle;
using t_ind_0 = Type::t_ind_0;
using iterator = Type::iterator;
using context = Type::context;
bool Type::insert(const t_tuple& t) {
context h;
return insert(t, h);
}
bool Type::insert(const t_tuple& t, context& h) {
if (ind_0.insert(t, h.hints_0_lower)) {
return true;
} else return false;
}
bool Type::insert(const RamDomain* ramDomain) {
RamDomain data[2];
std::copy(ramDomain, ramDomain + 2, data);
const t_tuple& tuple = reinterpret_cast<const t_tuple&>(data);
context h;
return insert(tuple, h);
}
bool Type::insert(RamDomain a0,RamDomain a1) {
RamDomain data[2] = {a0,a1};
return insert(data);
}
bool Type::contains(const t_tuple& t, context& h) const {
return ind_0.contains(t, h.hints_0_lower);
}
bool Type::contains(const t_tuple& t) const {
context h;
return contains(t, h);
}
std::size_t Type::size() const {
return ind_0.size();
}
iterator Type::find(const t_tuple& t, context& h) const {
return ind_0.find(t, h.hints_0_lower);
}
iterator Type::find(const t_tuple& t) const {
context h;
return find(t, h);
}
range<iterator> Type::lowerUpperRange_00(const t_tuple& /* lower */, const t_tuple& /* upper */, context& /* h */) const {
return range<iterator>(ind_0.begin(),ind_0.end());
}
range<iterator> Type::lowerUpperRange_00(const t_tuple& /* lower */, const t_tuple& /* upper */) const {
return range<iterator>(ind_0.begin(),ind_0.end());
}
range<t_ind_0::iterator> Type::lowerUpperRange_11(const t_tuple& lower, const t_tuple& upper, context& h) const {
t_comparator_0 comparator;
int cmp = comparator(lower, upper);
if (cmp == 0) {
    auto pos = ind_0.find(lower, h.hints_0_lower);
    auto fin = ind_0.end();
    if (pos != fin) {fin = pos; ++fin;}
    return make_range(pos, fin);
}
if (cmp > 0) {
    return make_range(ind_0.end(), ind_0.end());
}
return make_range(ind_0.lower_bound(lower, h.hints_0_lower), ind_0.upper_bound(upper, h.hints_0_upper));
}
range<t_ind_0::iterator> Type::lowerUpperRange_11(const t_tuple& lower, const t_tuple& upper) const {
context h;
return lowerUpperRange_11(lower,upper,h);
}
range<t_ind_0::iterator> Type::lowerUpperRange_10(const t_tuple& lower, const t_tuple& upper, context& h) const {
t_comparator_0 comparator;
int cmp = comparator(lower, upper);
if (cmp > 0) {
    return make_range(ind_0.end(), ind_0.end());
}
return make_range(ind_0.lower_bound(lower, h.hints_0_lower), ind_0.upper_bound(upper, h.hints_0_upper));
}
range<t_ind_0::iterator> Type::lowerUpperRange_10(const t_tuple& lower, const t_tuple& upper) const {
context h;
return lowerUpperRange_10(lower,upper,h);
}
bool Type::empty() const {
return ind_0.empty();
}
std::vector<range<iterator>> Type::partition() const {
return ind_0.getChunks(400);
}
void Type::purge() {
ind_0.clear();
}
iterator Type::begin() const {
return ind_0.begin();
}
iterator Type::end() const {
return ind_0.end();
}
void Type::printStatistics(std::ostream& o) const {
o << " arity 2 direct b-tree index 0 lex-order [0,1]\n";
ind_0.printStats(o);
}
} // namespace souffle::t_btree_000_ii__0_1__11__10 
namespace souffle::t_btree_000_i__0__1 {
using namespace souffle;
struct Type {
static constexpr Relation::arity_type Arity = 1;
using t_tuple = Tuple<RamDomain, 1>;
struct t_comparator_0{
 int operator()(const t_tuple& a, const t_tuple& b) const {
  return (ramBitCast<RamSigned>(a[0]) < ramBitCast<RamSigned>(b[0])) ? -1 : (ramBitCast<RamSigned>(a[0]) > ramBitCast<RamSigned>(b[0])) ? 1 :(0);
 }
bool less(const t_tuple& a, const t_tuple& b) const {
  return (ramBitCast<RamSigned>(a[0]) < ramBitCast<RamSigned>(b[0]));
 }
bool equal(const t_tuple& a, const t_tuple& b) const {
return (ramBitCast<RamSigned>(a[0]) == ramBitCast<RamSigned>(b[0]));
 }
};
using t_ind_0 = btree_set<t_tuple,t_comparator_0>;
t_ind_0 ind_0;
using iterator = t_ind_0::iterator;
struct context {
t_ind_0::operation_hints hints_0_lower;
t_ind_0::operation_hints hints_0_upper;
};
context createContext() { return context(); }
bool insert(const t_tuple& t);
bool insert(const t_tuple& t, context& h);
bool insert(const RamDomain* ramDomain);
bool insert(RamDomain a0);
bool contains(const t_tuple& t, context& h) const;
bool contains(const t_tuple& t) const;
std::size_t size() const;
iterator find(const t_tuple& t, context& h) const;
iterator find(const t_tuple& t) const;
range<iterator> lowerUpperRange_0(const t_tuple& /* lower */, const t_tuple& /* upper */, context& /* h */) const;
range<iterator> lowerUpperRange_0(const t_tuple& /* lower */, const t_tuple& /* upper */) const;
range<t_ind_0::iterator> lowerUpperRange_1(const t_tuple& lower, const t_tuple& upper, context& h) const;
range<t_ind_0::iterator> lowerUpperRange_1(const t_tuple& lower, const t_tuple& upper) const;
bool empty() const;
std::vector<range<iterator>> partition() const;
void purge();
iterator begin() const;
iterator end() const;
void printStatistics(std::ostream& o) const;
};
} // namespace souffle::t_btree_000_i__0__1 
namespace souffle::t_btree_000_i__0__1 {
using namespace souffle;
using t_ind_0 = Type::t_ind_0;
using iterator = Type::iterator;
using context = Type::context;
bool Type::insert(const t_tuple& t) {
context h;
return insert(t, h);
}
bool Type::insert(const t_tuple& t, context& h) {
if (ind_0.insert(t, h.hints_0_lower)) {
return true;
} else return false;
}
bool Type::insert(const RamDomain* ramDomain) {
RamDomain data[1];
std::copy(ramDomain, ramDomain + 1, data);
const t_tuple& tuple = reinterpret_cast<const t_tuple&>(data);
context h;
return insert(tuple, h);
}
bool Type::insert(RamDomain a0) {
RamDomain data[1] = {a0};
return insert(data);
}
bool Type::contains(const t_tuple& t, context& h) const {
return ind_0.contains(t, h.hints_0_lower);
}
bool Type::contains(const t_tuple& t) const {
context h;
return contains(t, h);
}
std::size_t Type::size() const {
return ind_0.size();
}
iterator Type::find(const t_tuple& t, context& h) const {
return ind_0.find(t, h.hints_0_lower);
}
iterator Type::find(const t_tuple& t) const {
context h;
return find(t, h);
}
range<iterator> Type::lowerUpperRange_0(const t_tuple& /* lower */, const t_tuple& /* upper */, context& /* h */) const {
return range<iterator>(ind_0.begin(),ind_0.end());
}
range<iterator> Type::lowerUpperRange_0(const t_tuple& /* lower */, const t_tuple& /* upper */) const {
return range<iterator>(ind_0.begin(),ind_0.end());
}
range<t_ind_0::iterator> Type::lowerUpperRange_1(const t_tuple& lower, const t_tuple& upper, context& h) const {
t_comparator_0 comparator;
int cmp = comparator(lower, upper);
if (cmp == 0) {
    auto pos = ind_0.find(lower, h.hints_0_lower);
    auto fin = ind_0.end();
    if (pos != fin) {fin = pos; ++fin;}
    return make_range(pos, fin);
}
if (cmp > 0) {
    return make_range(ind_0.end(), ind_0.end());
}
return make_range(ind_0.lower_bound(lower, h.hints_0_lower), ind_0.upper_bound(upper, h.hints_0_upper));
}
range<t_ind_0::iterator> Type::lowerUpperRange_1(const t_tuple& lower, const t_tuple& upper) const {
context h;
return lowerUpperRange_1(lower,upper,h);
}
bool Type::empty() const {
return ind_0.empty();
}
std::vector<range<iterator>> Type::partition() const {
return ind_0.getChunks(400);
}
void Type::purge() {
ind_0.clear();
}
iterator Type::begin() const {
return ind_0.begin();
}
iterator Type::end() const {
return ind_0.end();
}
void Type::printStatistics(std::ostream& o) const {
o << " arity 1 direct b-tree index 0 lex-order [0]\n";
ind_0.printStats(o);
}
} // namespace souffle::t_btree_000_i__0__1 
namespace souffle::t_btree_000_iii__0_1_2__111 {
using namespace souffle;
struct Type {
static constexpr Relation::arity_type Arity = 3;
using t_tuple = Tuple<RamDomain, 3>;
struct t_comparator_0{
 int operator()(const t_tuple& a, const t_tuple& b) const {
  return (ramBitCast<RamSigned>(a[0]) < ramBitCast<RamSigned>(b[0])) ? -1 : (ramBitCast<RamSigned>(a[0]) > ramBitCast<RamSigned>(b[0])) ? 1 :((ramBitCast<RamSigned>(a[1]) < ramBitCast<RamSigned>(b[1])) ? -1 : (ramBitCast<RamSigned>(a[1]) > ramBitCast<RamSigned>(b[1])) ? 1 :((ramBitCast<RamSigned>(a[2]) < ramBitCast<RamSigned>(b[2])) ? -1 : (ramBitCast<RamSigned>(a[2]) > ramBitCast<RamSigned>(b[2])) ? 1 :(0)));
 }
bool less(const t_tuple& a, const t_tuple& b) const {
  return (ramBitCast<RamSigned>(a[0]) < ramBitCast<RamSigned>(b[0]))|| ((ramBitCast<RamSigned>(a[0]) == ramBitCast<RamSigned>(b[0])) && ((ramBitCast<RamSigned>(a[1]) < ramBitCast<RamSigned>(b[1]))|| ((ramBitCast<RamSigned>(a[1]) == ramBitCast<RamSigned>(b[1])) && ((ramBitCast<RamSigned>(a[2]) < ramBitCast<RamSigned>(b[2]))))));
 }
bool equal(const t_tuple& a, const t_tuple& b) const {
return (ramBitCast<RamSigned>(a[0]) == ramBitCast<RamSigned>(b[0]))&&(ramBitCast<RamSigned>(a[1]) == ramBitCast<RamSigned>(b[1]))&&(ramBitCast<RamSigned>(a[2]) == ramBitCast<RamSigned>(b[2]));
 }
};
using t_ind_0 = btree_set<t_tuple,t_comparator_0>;
t_ind_0 ind_0;
using iterator = t_ind_0::iterator;
struct context {
t_ind_0::operation_hints hints_0_lower;
t_ind_0::operation_hints hints_0_upper;
};
context createContext() { return context(); }
bool insert(const t_tuple& t);
bool insert(const t_tuple& t, context& h);
bool insert(const RamDomain* ramDomain);
bool insert(RamDomain a0,RamDomain a1,RamDomain a2);
bool contains(const t_tuple& t, context& h) const;
bool contains(const t_tuple& t) const;
std::size_t size() const;
iterator find(const t_tuple& t, context& h) const;
iterator find(const t_tuple& t) const;
range<iterator> lowerUpperRange_000(const t_tuple& /* lower */, const t_tuple& /* upper */, context& /* h */) const;
range<iterator> lowerUpperRange_000(const t_tuple& /* lower */, const t_tuple& /* upper */) const;
range<t_ind_0::iterator> lowerUpperRange_111(const t_tuple& lower, const t_tuple& upper, context& h) const;
range<t_ind_0::iterator> lowerUpperRange_111(const t_tuple& lower, const t_tuple& upper) const;
bool empty() const;
std::vector<range<iterator>> partition() const;
void purge();
iterator begin() const;
iterator end() const;
void printStatistics(std::ostream& o) const;
};
} // namespace souffle::t_btree_000_iii__0_1_2__111 
namespace souffle::t_btree_000_iii__0_1_2__111 {
using namespace souffle;
using t_ind_0 = Type::t_ind_0;
using iterator = Type::iterator;
using context = Type::context;
bool Type::insert(const t_tuple& t) {
context h;
return insert(t, h);
}
bool Type::insert(const t_tuple& t, context& h) {
if (ind_0.insert(t, h.hints_0_lower)) {
return true;
} else return false;
}
bool Type::insert(const RamDomain* ramDomain) {
RamDomain data[3];
std::copy(ramDomain, ramDomain + 3, data);
const t_tuple& tuple = reinterpret_cast<const t_tuple&>(data);
context h;
return insert(tuple, h);
}
bool Type::insert(RamDomain a0,RamDomain a1,RamDomain a2) {
RamDomain data[3] = {a0,a1,a2};
return insert(data);
}
bool Type::contains(const t_tuple& t, context& h) const {
return ind_0.contains(t, h.hints_0_lower);
}
bool Type::contains(const t_tuple& t) const {
context h;
return contains(t, h);
}
std::size_t Type::size() const {
return ind_0.size();
}
iterator Type::find(const t_tuple& t, context& h) const {
return ind_0.find(t, h.hints_0_lower);
}
iterator Type::find(const t_tuple& t) const {
context h;
return find(t, h);
}
range<iterator> Type::lowerUpperRange_000(const t_tuple& /* lower */, const t_tuple& /* upper */, context& /* h */) const {
return range<iterator>(ind_0.begin(),ind_0.end());
}
range<iterator> Type::lowerUpperRange_000(const t_tuple& /* lower */, const t_tuple& /* upper */) const {
return range<iterator>(ind_0.begin(),ind_0.end());
}
range<t_ind_0::iterator> Type::lowerUpperRange_111(const t_tuple& lower, const t_tuple& upper, context& h) const {
t_comparator_0 comparator;
int cmp = comparator(lower, upper);
if (cmp == 0) {
    auto pos = ind_0.find(lower, h.hints_0_lower);
    auto fin = ind_0.end();
    if (pos != fin) {fin = pos; ++fin;}
    return make_range(pos, fin);
}
if (cmp > 0) {
    return make_range(ind_0.end(), ind_0.end());
}
return make_range(ind_0.lower_bound(lower, h.hints_0_lower), ind_0.upper_bound(upper, h.hints_0_upper));
}
range<t_ind_0::iterator> Type::lowerUpperRange_111(const t_tuple& lower, const t_tuple& upper) const {
context h;
return lowerUpperRange_111(lower,upper,h);
}
bool Type::empty() const {
return ind_0.empty();
}
std::vector<range<iterator>> Type::partition() const {
return ind_0.getChunks(400);
}
void Type::purge() {
ind_0.clear();
}
iterator Type::begin() const {
return ind_0.begin();
}
iterator Type::end() const {
return ind_0.end();
}
void Type::printStatistics(std::ostream& o) const {
o << " arity 3 direct b-tree index 0 lex-order [0,1,2]\n";
ind_0.printStats(o);
}
} // namespace souffle::t_btree_000_iii__0_1_2__111 
namespace  souffle {
using namespace souffle;
class Stratum_interm_out_violation_fff__1031d5952eeac068 {
public:
 Stratum_interm_out_violation_fff__1031d5952eeac068(SymbolTable& symTable,RecordTable& recordTable,ConcurrentCache<std::string,std::regex>& regexCache,bool& pruneImdtRels,bool& performIO,SignalHandler*& signalHandler,std::atomic<std::size_t>& iter,std::atomic<RamDomain>& ctr,std::string& inputDirectory,std::string& outputDirectory,t_btree_000_iii__0_1_2__111::Type& rel_interm_out_violation_fff__bda2c2e8e8813350,t_nullaries& rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06,t_btree_000_i__0__1::Type& rel_neglabel_has_name_be2950f430dab32a,t_btree_000_i__0__1::Type& rel_neglabel_has_occupation_f0e827e7bbd5a7f2,t_btree_000_ii__0_1__11__10::Type& rel_birthDate_9bc1888ef26605d0,t_btree_000_ii__0_1__11__10::Type& rel_deathDate_2a1e0db35f240968,t_btree_000_ii__0_1__11__10::Type& rel_name_58440f57e1b2dd1f,t_btree_000_ii__0_1__11__10::Type& rel_nationality_45001e24d435ebbf,t_btree_000_ii__0_1__11__10::Type& rel_occupation_76c3c68cff8238ec,t_btree_000_i__0__1::Type& rel_person_4b7efb71e7bbaeee);
void run([[maybe_unused]] const std::vector<RamDomain>& args,[[maybe_unused]] std::vector<RamDomain>& ret);
private:
SymbolTable& symTable;
RecordTable& recordTable;
ConcurrentCache<std::string,std::regex>& regexCache;
bool& pruneImdtRels;
bool& performIO;
SignalHandler*& signalHandler;
std::atomic<std::size_t>& iter;
std::atomic<RamDomain>& ctr;
std::string& inputDirectory;
std::string& outputDirectory;
t_btree_000_iii__0_1_2__111::Type* rel_interm_out_violation_fff__bda2c2e8e8813350;
t_nullaries* rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06;
t_btree_000_i__0__1::Type* rel_neglabel_has_name_be2950f430dab32a;
t_btree_000_i__0__1::Type* rel_neglabel_has_occupation_f0e827e7bbd5a7f2;
t_btree_000_ii__0_1__11__10::Type* rel_birthDate_9bc1888ef26605d0;
t_btree_000_ii__0_1__11__10::Type* rel_deathDate_2a1e0db35f240968;
t_btree_000_ii__0_1__11__10::Type* rel_name_58440f57e1b2dd1f;
t_btree_000_ii__0_1__11__10::Type* rel_nationality_45001e24d435ebbf;
t_btree_000_ii__0_1__11__10::Type* rel_occupation_76c3c68cff8238ec;
t_btree_000_i__0__1::Type* rel_person_4b7efb71e7bbaeee;
};
} // namespace  souffle
namespace  souffle {
using namespace souffle;
 Stratum_interm_out_violation_fff__1031d5952eeac068::Stratum_interm_out_violation_fff__1031d5952eeac068(SymbolTable& symTable,RecordTable& recordTable,ConcurrentCache<std::string,std::regex>& regexCache,bool& pruneImdtRels,bool& performIO,SignalHandler*& signalHandler,std::atomic<std::size_t>& iter,std::atomic<RamDomain>& ctr,std::string& inputDirectory,std::string& outputDirectory,t_btree_000_iii__0_1_2__111::Type& rel_interm_out_violation_fff__bda2c2e8e8813350,t_nullaries& rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06,t_btree_000_i__0__1::Type& rel_neglabel_has_name_be2950f430dab32a,t_btree_000_i__0__1::Type& rel_neglabel_has_occupation_f0e827e7bbd5a7f2,t_btree_000_ii__0_1__11__10::Type& rel_birthDate_9bc1888ef26605d0,t_btree_000_ii__0_1__11__10::Type& rel_deathDate_2a1e0db35f240968,t_btree_000_ii__0_1__11__10::Type& rel_name_58440f57e1b2dd1f,t_btree_000_ii__0_1__11__10::Type& rel_nationality_45001e24d435ebbf,t_btree_000_ii__0_1__11__10::Type& rel_occupation_76c3c68cff8238ec,t_btree_000_i__0__1::Type& rel_person_4b7efb71e7bbaeee):
symTable(symTable),
recordTable(recordTable),
regexCache(regexCache),
pruneImdtRels(pruneImdtRels),
performIO(performIO),
signalHandler(signalHandler),
iter(iter),
ctr(ctr),
inputDirectory(inputDirectory),
outputDirectory(outputDirectory),
rel_interm_out_violation_fff__bda2c2e8e8813350(&rel_interm_out_violation_fff__bda2c2e8e8813350),
rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06(&rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06),
rel_neglabel_has_name_be2950f430dab32a(&rel_neglabel_has_name_be2950f430dab32a),
rel_neglabel_has_occupation_f0e827e7bbd5a7f2(&rel_neglabel_has_occupation_f0e827e7bbd5a7f2),
rel_birthDate_9bc1888ef26605d0(&rel_birthDate_9bc1888ef26605d0),
rel_deathDate_2a1e0db35f240968(&rel_deathDate_2a1e0db35f240968),
rel_name_58440f57e1b2dd1f(&rel_name_58440f57e1b2dd1f),
rel_nationality_45001e24d435ebbf(&rel_nationality_45001e24d435ebbf),
rel_occupation_76c3c68cff8238ec(&rel_occupation_76c3c68cff8238ec),
rel_person_4b7efb71e7bbaeee(&rel_person_4b7efb71e7bbaeee){
}

void Stratum_interm_out_violation_fff__1031d5952eeac068::run([[maybe_unused]] const std::vector<RamDomain>& args,[[maybe_unused]] std::vector<RamDomain>& ret){
signalHandler->setMsg(R"_(@interm_out.violation.{fff}(E,"minCount","Person must have a valid name") :- 
   @magic.@interm_out.violation.{fff}(),
   person(E),
   !@neglabel.has_name(E).
in file  [1:1-1:1])_");
if(!(rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06->empty()) && !(rel_person_4b7efb71e7bbaeee->empty())) {
[&](){
auto part = rel_person_4b7efb71e7bbaeee->partition();
PARALLEL_START
CREATE_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt,rel_interm_out_violation_fff__bda2c2e8e8813350->createContext());
CREATE_OP_CONTEXT(rel_neglabel_has_name_be2950f430dab32a_op_ctxt,rel_neglabel_has_name_be2950f430dab32a->createContext());
CREATE_OP_CONTEXT(rel_person_4b7efb71e7bbaeee_op_ctxt,rel_person_4b7efb71e7bbaeee->createContext());

                   #if defined _OPENMP && _OPENMP < 200805
                           auto count = std::distance(part.begin(), part.end());
                           auto base = part.begin();
                           pfor(int index  = 0; index < count; index++) {
                               auto it = base + index;
                   #else
                           pfor(auto it = part.begin(); it < part.end(); it++) {
                   #endif
                   try{
for(const auto& env0 : *it) {
if( !(rel_neglabel_has_name_be2950f430dab32a->contains(Tuple<RamDomain,1>{{ramBitCast(env0[0])}},READ_OP_CONTEXT(rel_neglabel_has_name_be2950f430dab32a_op_ctxt)))) {
Tuple<RamDomain,3> tuple{{ramBitCast(env0[0]),ramBitCast(RamSigned(0)),ramBitCast(RamSigned(1))}};
rel_interm_out_violation_fff__bda2c2e8e8813350->insert(tuple,READ_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt));
}
}
} catch(std::exception &e) { signalHandler->error(e.what());}
}
PARALLEL_END
}
();}
signalHandler->setMsg(R"_(@interm_out.violation.{fff}(E,"maxCount","Person must have a valid name") :- 
   @magic.@interm_out.violation.{fff}(),
   person(E),
   name(E,V1),
   name(E,V2),
   V1 != V2.
in file  [1:1-1:1])_");
if(!(rel_name_58440f57e1b2dd1f->empty()) && !(rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06->empty()) && !(rel_person_4b7efb71e7bbaeee->empty())) {
[&](){
auto part = rel_person_4b7efb71e7bbaeee->partition();
PARALLEL_START
CREATE_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt,rel_interm_out_violation_fff__bda2c2e8e8813350->createContext());
CREATE_OP_CONTEXT(rel_name_58440f57e1b2dd1f_op_ctxt,rel_name_58440f57e1b2dd1f->createContext());
CREATE_OP_CONTEXT(rel_person_4b7efb71e7bbaeee_op_ctxt,rel_person_4b7efb71e7bbaeee->createContext());

                   #if defined _OPENMP && _OPENMP < 200805
                           auto count = std::distance(part.begin(), part.end());
                           auto base = part.begin();
                           pfor(int index  = 0; index < count; index++) {
                               auto it = base + index;
                   #else
                           pfor(auto it = part.begin(); it < part.end(); it++) {
                   #endif
                   try{
for(const auto& env0 : *it) {
auto range = rel_name_58440f57e1b2dd1f->lowerUpperRange_10(Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MIN_RAM_SIGNED)}},Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MAX_RAM_SIGNED)}},READ_OP_CONTEXT(rel_name_58440f57e1b2dd1f_op_ctxt));
for(const auto& env1 : range) {
auto range = rel_name_58440f57e1b2dd1f->lowerUpperRange_10(Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MIN_RAM_SIGNED)}},Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MAX_RAM_SIGNED)}},READ_OP_CONTEXT(rel_name_58440f57e1b2dd1f_op_ctxt));
for(const auto& env2 : range) {
if( (ramBitCast<RamDomain>(env1[1]) != ramBitCast<RamDomain>(env2[1]))) {
Tuple<RamDomain,3> tuple{{ramBitCast(env0[0]),ramBitCast(RamSigned(2)),ramBitCast(RamSigned(1))}};
rel_interm_out_violation_fff__bda2c2e8e8813350->insert(tuple,READ_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt));
break;
}
}
}
}
} catch(std::exception &e) { signalHandler->error(e.what());}
}
PARALLEL_END
}
();}
signalHandler->setMsg(R"_(@interm_out.violation.{fff}(E,"minLength","Person must have a valid name") :- 
   @magic.@interm_out.violation.{fff}(),
   person(E),
   name(E,V),
   strlen(V) < 1.
in file  [1:1-1:1])_");
if(!(rel_person_4b7efb71e7bbaeee->empty()) && !(rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06->empty()) && !(rel_name_58440f57e1b2dd1f->empty())) {
[&](){
auto part = rel_person_4b7efb71e7bbaeee->partition();
PARALLEL_START
CREATE_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt,rel_interm_out_violation_fff__bda2c2e8e8813350->createContext());
CREATE_OP_CONTEXT(rel_name_58440f57e1b2dd1f_op_ctxt,rel_name_58440f57e1b2dd1f->createContext());
CREATE_OP_CONTEXT(rel_person_4b7efb71e7bbaeee_op_ctxt,rel_person_4b7efb71e7bbaeee->createContext());

                   #if defined _OPENMP && _OPENMP < 200805
                           auto count = std::distance(part.begin(), part.end());
                           auto base = part.begin();
                           pfor(int index  = 0; index < count; index++) {
                               auto it = base + index;
                   #else
                           pfor(auto it = part.begin(); it < part.end(); it++) {
                   #endif
                   try{
for(const auto& env0 : *it) {
auto range = rel_name_58440f57e1b2dd1f->lowerUpperRange_10(Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MIN_RAM_SIGNED)}},Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MAX_RAM_SIGNED)}},READ_OP_CONTEXT(rel_name_58440f57e1b2dd1f_op_ctxt));
for(const auto& env1 : range) {
if( (ramBitCast<RamSigned>(static_cast<RamSigned>(symTable.decode(env1[1]).size())) < ramBitCast<RamSigned>(RamSigned(1)))) {
Tuple<RamDomain,3> tuple{{ramBitCast(env0[0]),ramBitCast(RamSigned(3)),ramBitCast(RamSigned(1))}};
rel_interm_out_violation_fff__bda2c2e8e8813350->insert(tuple,READ_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt));
break;
}
}
}
} catch(std::exception &e) { signalHandler->error(e.what());}
}
PARALLEL_END
}
();}
signalHandler->setMsg(R"_(@interm_out.violation.{fff}(E,"maxLength","Person must have a valid name") :- 
   @magic.@interm_out.violation.{fff}(),
   person(E),
   name(E,V),
   strlen(V) > 300.
in file  [1:1-1:1])_");
if(!(rel_person_4b7efb71e7bbaeee->empty()) && !(rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06->empty()) && !(rel_name_58440f57e1b2dd1f->empty())) {
[&](){
auto part = rel_person_4b7efb71e7bbaeee->partition();
PARALLEL_START
CREATE_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt,rel_interm_out_violation_fff__bda2c2e8e8813350->createContext());
CREATE_OP_CONTEXT(rel_name_58440f57e1b2dd1f_op_ctxt,rel_name_58440f57e1b2dd1f->createContext());
CREATE_OP_CONTEXT(rel_person_4b7efb71e7bbaeee_op_ctxt,rel_person_4b7efb71e7bbaeee->createContext());

                   #if defined _OPENMP && _OPENMP < 200805
                           auto count = std::distance(part.begin(), part.end());
                           auto base = part.begin();
                           pfor(int index  = 0; index < count; index++) {
                               auto it = base + index;
                   #else
                           pfor(auto it = part.begin(); it < part.end(); it++) {
                   #endif
                   try{
for(const auto& env0 : *it) {
auto range = rel_name_58440f57e1b2dd1f->lowerUpperRange_10(Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MIN_RAM_SIGNED)}},Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MAX_RAM_SIGNED)}},READ_OP_CONTEXT(rel_name_58440f57e1b2dd1f_op_ctxt));
for(const auto& env1 : range) {
if( (ramBitCast<RamSigned>(static_cast<RamSigned>(symTable.decode(env1[1]).size())) > ramBitCast<RamSigned>(RamSigned(300)))) {
Tuple<RamDomain,3> tuple{{ramBitCast(env0[0]),ramBitCast(RamSigned(4)),ramBitCast(RamSigned(1))}};
rel_interm_out_violation_fff__bda2c2e8e8813350->insert(tuple,READ_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt));
break;
}
}
}
} catch(std::exception &e) { signalHandler->error(e.what());}
}
PARALLEL_END
}
();}
signalHandler->setMsg(R"_(@interm_out.violation.{fff}(E,"minCount","Person must have at least one occupation") :- 
   @magic.@interm_out.violation.{fff}(),
   person(E),
   !@neglabel.has_occupation(E).
in file  [1:1-1:1])_");
if(!(rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06->empty()) && !(rel_person_4b7efb71e7bbaeee->empty())) {
[&](){
auto part = rel_person_4b7efb71e7bbaeee->partition();
PARALLEL_START
CREATE_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt,rel_interm_out_violation_fff__bda2c2e8e8813350->createContext());
CREATE_OP_CONTEXT(rel_neglabel_has_occupation_f0e827e7bbd5a7f2_op_ctxt,rel_neglabel_has_occupation_f0e827e7bbd5a7f2->createContext());
CREATE_OP_CONTEXT(rel_person_4b7efb71e7bbaeee_op_ctxt,rel_person_4b7efb71e7bbaeee->createContext());

                   #if defined _OPENMP && _OPENMP < 200805
                           auto count = std::distance(part.begin(), part.end());
                           auto base = part.begin();
                           pfor(int index  = 0; index < count; index++) {
                               auto it = base + index;
                   #else
                           pfor(auto it = part.begin(); it < part.end(); it++) {
                   #endif
                   try{
for(const auto& env0 : *it) {
if( !(rel_neglabel_has_occupation_f0e827e7bbd5a7f2->contains(Tuple<RamDomain,1>{{ramBitCast(env0[0])}},READ_OP_CONTEXT(rel_neglabel_has_occupation_f0e827e7bbd5a7f2_op_ctxt)))) {
Tuple<RamDomain,3> tuple{{ramBitCast(env0[0]),ramBitCast(RamSigned(0)),ramBitCast(RamSigned(5))}};
rel_interm_out_violation_fff__bda2c2e8e8813350->insert(tuple,READ_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt));
}
}
} catch(std::exception &e) { signalHandler->error(e.what());}
}
PARALLEL_END
}
();}
signalHandler->setMsg(R"_(@interm_out.violation.{fff}(E,"minLength","Person must have at least one occupation") :- 
   @magic.@interm_out.violation.{fff}(),
   person(E),
   occupation(E,V),
   strlen(V) < 1.
in file  [1:1-1:1])_");
if(!(rel_person_4b7efb71e7bbaeee->empty()) && !(rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06->empty()) && !(rel_occupation_76c3c68cff8238ec->empty())) {
[&](){
auto part = rel_person_4b7efb71e7bbaeee->partition();
PARALLEL_START
CREATE_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt,rel_interm_out_violation_fff__bda2c2e8e8813350->createContext());
CREATE_OP_CONTEXT(rel_occupation_76c3c68cff8238ec_op_ctxt,rel_occupation_76c3c68cff8238ec->createContext());
CREATE_OP_CONTEXT(rel_person_4b7efb71e7bbaeee_op_ctxt,rel_person_4b7efb71e7bbaeee->createContext());

                   #if defined _OPENMP && _OPENMP < 200805
                           auto count = std::distance(part.begin(), part.end());
                           auto base = part.begin();
                           pfor(int index  = 0; index < count; index++) {
                               auto it = base + index;
                   #else
                           pfor(auto it = part.begin(); it < part.end(); it++) {
                   #endif
                   try{
for(const auto& env0 : *it) {
auto range = rel_occupation_76c3c68cff8238ec->lowerUpperRange_10(Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MIN_RAM_SIGNED)}},Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MAX_RAM_SIGNED)}},READ_OP_CONTEXT(rel_occupation_76c3c68cff8238ec_op_ctxt));
for(const auto& env1 : range) {
if( (ramBitCast<RamSigned>(static_cast<RamSigned>(symTable.decode(env1[1]).size())) < ramBitCast<RamSigned>(RamSigned(1)))) {
Tuple<RamDomain,3> tuple{{ramBitCast(env0[0]),ramBitCast(RamSigned(3)),ramBitCast(RamSigned(5))}};
rel_interm_out_violation_fff__bda2c2e8e8813350->insert(tuple,READ_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt));
break;
}
}
}
} catch(std::exception &e) { signalHandler->error(e.what());}
}
PARALLEL_END
}
();}
signalHandler->setMsg(R"_(@interm_out.violation.{fff}(E,"maxCount","Birth date must be reasonable format") :- 
   @magic.@interm_out.violation.{fff}(),
   person(E),
   birthDate(E,V1),
   birthDate(E,V2),
   V1 != V2.
in file  [1:1-1:1])_");
if(!(rel_birthDate_9bc1888ef26605d0->empty()) && !(rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06->empty()) && !(rel_person_4b7efb71e7bbaeee->empty())) {
[&](){
auto part = rel_person_4b7efb71e7bbaeee->partition();
PARALLEL_START
CREATE_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt,rel_interm_out_violation_fff__bda2c2e8e8813350->createContext());
CREATE_OP_CONTEXT(rel_birthDate_9bc1888ef26605d0_op_ctxt,rel_birthDate_9bc1888ef26605d0->createContext());
CREATE_OP_CONTEXT(rel_person_4b7efb71e7bbaeee_op_ctxt,rel_person_4b7efb71e7bbaeee->createContext());

                   #if defined _OPENMP && _OPENMP < 200805
                           auto count = std::distance(part.begin(), part.end());
                           auto base = part.begin();
                           pfor(int index  = 0; index < count; index++) {
                               auto it = base + index;
                   #else
                           pfor(auto it = part.begin(); it < part.end(); it++) {
                   #endif
                   try{
for(const auto& env0 : *it) {
auto range = rel_birthDate_9bc1888ef26605d0->lowerUpperRange_10(Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MIN_RAM_SIGNED)}},Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MAX_RAM_SIGNED)}},READ_OP_CONTEXT(rel_birthDate_9bc1888ef26605d0_op_ctxt));
for(const auto& env1 : range) {
auto range = rel_birthDate_9bc1888ef26605d0->lowerUpperRange_10(Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MIN_RAM_SIGNED)}},Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MAX_RAM_SIGNED)}},READ_OP_CONTEXT(rel_birthDate_9bc1888ef26605d0_op_ctxt));
for(const auto& env2 : range) {
if( (ramBitCast<RamDomain>(env1[1]) != ramBitCast<RamDomain>(env2[1]))) {
Tuple<RamDomain,3> tuple{{ramBitCast(env0[0]),ramBitCast(RamSigned(2)),ramBitCast(RamSigned(6))}};
rel_interm_out_violation_fff__bda2c2e8e8813350->insert(tuple,READ_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt));
break;
}
}
}
}
} catch(std::exception &e) { signalHandler->error(e.what());}
}
PARALLEL_END
}
();}
signalHandler->setMsg(R"_(@interm_out.violation.{fff}(E,"minLength","Birth date must be reasonable format") :- 
   @magic.@interm_out.violation.{fff}(),
   person(E),
   birthDate(E,V),
   strlen(V) < 4.
in file  [1:1-1:1])_");
if(!(rel_person_4b7efb71e7bbaeee->empty()) && !(rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06->empty()) && !(rel_birthDate_9bc1888ef26605d0->empty())) {
[&](){
auto part = rel_person_4b7efb71e7bbaeee->partition();
PARALLEL_START
CREATE_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt,rel_interm_out_violation_fff__bda2c2e8e8813350->createContext());
CREATE_OP_CONTEXT(rel_birthDate_9bc1888ef26605d0_op_ctxt,rel_birthDate_9bc1888ef26605d0->createContext());
CREATE_OP_CONTEXT(rel_person_4b7efb71e7bbaeee_op_ctxt,rel_person_4b7efb71e7bbaeee->createContext());

                   #if defined _OPENMP && _OPENMP < 200805
                           auto count = std::distance(part.begin(), part.end());
                           auto base = part.begin();
                           pfor(int index  = 0; index < count; index++) {
                               auto it = base + index;
                   #else
                           pfor(auto it = part.begin(); it < part.end(); it++) {
                   #endif
                   try{
for(const auto& env0 : *it) {
auto range = rel_birthDate_9bc1888ef26605d0->lowerUpperRange_10(Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MIN_RAM_SIGNED)}},Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MAX_RAM_SIGNED)}},READ_OP_CONTEXT(rel_birthDate_9bc1888ef26605d0_op_ctxt));
for(const auto& env1 : range) {
if( (ramBitCast<RamSigned>(static_cast<RamSigned>(symTable.decode(env1[1]).size())) < ramBitCast<RamSigned>(RamSigned(4)))) {
Tuple<RamDomain,3> tuple{{ramBitCast(env0[0]),ramBitCast(RamSigned(3)),ramBitCast(RamSigned(6))}};
rel_interm_out_violation_fff__bda2c2e8e8813350->insert(tuple,READ_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt));
break;
}
}
}
} catch(std::exception &e) { signalHandler->error(e.what());}
}
PARALLEL_END
}
();}
signalHandler->setMsg(R"_(@interm_out.violation.{fff}(E,"maxLength","Birth date must be reasonable format") :- 
   @magic.@interm_out.violation.{fff}(),
   person(E),
   birthDate(E,V),
   strlen(V) > 25.
in file  [1:1-1:1])_");
if(!(rel_person_4b7efb71e7bbaeee->empty()) && !(rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06->empty()) && !(rel_birthDate_9bc1888ef26605d0->empty())) {
[&](){
auto part = rel_person_4b7efb71e7bbaeee->partition();
PARALLEL_START
CREATE_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt,rel_interm_out_violation_fff__bda2c2e8e8813350->createContext());
CREATE_OP_CONTEXT(rel_birthDate_9bc1888ef26605d0_op_ctxt,rel_birthDate_9bc1888ef26605d0->createContext());
CREATE_OP_CONTEXT(rel_person_4b7efb71e7bbaeee_op_ctxt,rel_person_4b7efb71e7bbaeee->createContext());

                   #if defined _OPENMP && _OPENMP < 200805
                           auto count = std::distance(part.begin(), part.end());
                           auto base = part.begin();
                           pfor(int index  = 0; index < count; index++) {
                               auto it = base + index;
                   #else
                           pfor(auto it = part.begin(); it < part.end(); it++) {
                   #endif
                   try{
for(const auto& env0 : *it) {
auto range = rel_birthDate_9bc1888ef26605d0->lowerUpperRange_10(Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MIN_RAM_SIGNED)}},Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MAX_RAM_SIGNED)}},READ_OP_CONTEXT(rel_birthDate_9bc1888ef26605d0_op_ctxt));
for(const auto& env1 : range) {
if( (ramBitCast<RamSigned>(static_cast<RamSigned>(symTable.decode(env1[1]).size())) > ramBitCast<RamSigned>(RamSigned(25)))) {
Tuple<RamDomain,3> tuple{{ramBitCast(env0[0]),ramBitCast(RamSigned(4)),ramBitCast(RamSigned(6))}};
rel_interm_out_violation_fff__bda2c2e8e8813350->insert(tuple,READ_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt));
break;
}
}
}
} catch(std::exception &e) { signalHandler->error(e.what());}
}
PARALLEL_END
}
();}
signalHandler->setMsg(R"_(@interm_out.violation.{fff}(E,"maxCount","Death date must be reasonable format") :- 
   @magic.@interm_out.violation.{fff}(),
   person(E),
   deathDate(E,V1),
   deathDate(E,V2),
   V1 != V2.
in file  [1:1-1:1])_");
if(!(rel_deathDate_2a1e0db35f240968->empty()) && !(rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06->empty()) && !(rel_person_4b7efb71e7bbaeee->empty())) {
[&](){
auto part = rel_person_4b7efb71e7bbaeee->partition();
PARALLEL_START
CREATE_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt,rel_interm_out_violation_fff__bda2c2e8e8813350->createContext());
CREATE_OP_CONTEXT(rel_deathDate_2a1e0db35f240968_op_ctxt,rel_deathDate_2a1e0db35f240968->createContext());
CREATE_OP_CONTEXT(rel_person_4b7efb71e7bbaeee_op_ctxt,rel_person_4b7efb71e7bbaeee->createContext());

                   #if defined _OPENMP && _OPENMP < 200805
                           auto count = std::distance(part.begin(), part.end());
                           auto base = part.begin();
                           pfor(int index  = 0; index < count; index++) {
                               auto it = base + index;
                   #else
                           pfor(auto it = part.begin(); it < part.end(); it++) {
                   #endif
                   try{
for(const auto& env0 : *it) {
auto range = rel_deathDate_2a1e0db35f240968->lowerUpperRange_10(Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MIN_RAM_SIGNED)}},Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MAX_RAM_SIGNED)}},READ_OP_CONTEXT(rel_deathDate_2a1e0db35f240968_op_ctxt));
for(const auto& env1 : range) {
auto range = rel_deathDate_2a1e0db35f240968->lowerUpperRange_10(Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MIN_RAM_SIGNED)}},Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MAX_RAM_SIGNED)}},READ_OP_CONTEXT(rel_deathDate_2a1e0db35f240968_op_ctxt));
for(const auto& env2 : range) {
if( (ramBitCast<RamDomain>(env1[1]) != ramBitCast<RamDomain>(env2[1]))) {
Tuple<RamDomain,3> tuple{{ramBitCast(env0[0]),ramBitCast(RamSigned(2)),ramBitCast(RamSigned(7))}};
rel_interm_out_violation_fff__bda2c2e8e8813350->insert(tuple,READ_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt));
break;
}
}
}
}
} catch(std::exception &e) { signalHandler->error(e.what());}
}
PARALLEL_END
}
();}
signalHandler->setMsg(R"_(@interm_out.violation.{fff}(E,"minLength","Death date must be reasonable format") :- 
   @magic.@interm_out.violation.{fff}(),
   person(E),
   deathDate(E,V),
   strlen(V) < 4.
in file  [1:1-1:1])_");
if(!(rel_person_4b7efb71e7bbaeee->empty()) && !(rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06->empty()) && !(rel_deathDate_2a1e0db35f240968->empty())) {
[&](){
auto part = rel_person_4b7efb71e7bbaeee->partition();
PARALLEL_START
CREATE_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt,rel_interm_out_violation_fff__bda2c2e8e8813350->createContext());
CREATE_OP_CONTEXT(rel_deathDate_2a1e0db35f240968_op_ctxt,rel_deathDate_2a1e0db35f240968->createContext());
CREATE_OP_CONTEXT(rel_person_4b7efb71e7bbaeee_op_ctxt,rel_person_4b7efb71e7bbaeee->createContext());

                   #if defined _OPENMP && _OPENMP < 200805
                           auto count = std::distance(part.begin(), part.end());
                           auto base = part.begin();
                           pfor(int index  = 0; index < count; index++) {
                               auto it = base + index;
                   #else
                           pfor(auto it = part.begin(); it < part.end(); it++) {
                   #endif
                   try{
for(const auto& env0 : *it) {
auto range = rel_deathDate_2a1e0db35f240968->lowerUpperRange_10(Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MIN_RAM_SIGNED)}},Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MAX_RAM_SIGNED)}},READ_OP_CONTEXT(rel_deathDate_2a1e0db35f240968_op_ctxt));
for(const auto& env1 : range) {
if( (ramBitCast<RamSigned>(static_cast<RamSigned>(symTable.decode(env1[1]).size())) < ramBitCast<RamSigned>(RamSigned(4)))) {
Tuple<RamDomain,3> tuple{{ramBitCast(env0[0]),ramBitCast(RamSigned(3)),ramBitCast(RamSigned(7))}};
rel_interm_out_violation_fff__bda2c2e8e8813350->insert(tuple,READ_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt));
break;
}
}
}
} catch(std::exception &e) { signalHandler->error(e.what());}
}
PARALLEL_END
}
();}
signalHandler->setMsg(R"_(@interm_out.violation.{fff}(E,"maxLength","Death date must be reasonable format") :- 
   @magic.@interm_out.violation.{fff}(),
   person(E),
   deathDate(E,V),
   strlen(V) > 25.
in file  [1:1-1:1])_");
if(!(rel_person_4b7efb71e7bbaeee->empty()) && !(rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06->empty()) && !(rel_deathDate_2a1e0db35f240968->empty())) {
[&](){
auto part = rel_person_4b7efb71e7bbaeee->partition();
PARALLEL_START
CREATE_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt,rel_interm_out_violation_fff__bda2c2e8e8813350->createContext());
CREATE_OP_CONTEXT(rel_deathDate_2a1e0db35f240968_op_ctxt,rel_deathDate_2a1e0db35f240968->createContext());
CREATE_OP_CONTEXT(rel_person_4b7efb71e7bbaeee_op_ctxt,rel_person_4b7efb71e7bbaeee->createContext());

                   #if defined _OPENMP && _OPENMP < 200805
                           auto count = std::distance(part.begin(), part.end());
                           auto base = part.begin();
                           pfor(int index  = 0; index < count; index++) {
                               auto it = base + index;
                   #else
                           pfor(auto it = part.begin(); it < part.end(); it++) {
                   #endif
                   try{
for(const auto& env0 : *it) {
auto range = rel_deathDate_2a1e0db35f240968->lowerUpperRange_10(Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MIN_RAM_SIGNED)}},Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MAX_RAM_SIGNED)}},READ_OP_CONTEXT(rel_deathDate_2a1e0db35f240968_op_ctxt));
for(const auto& env1 : range) {
if( (ramBitCast<RamSigned>(static_cast<RamSigned>(symTable.decode(env1[1]).size())) > ramBitCast<RamSigned>(RamSigned(25)))) {
Tuple<RamDomain,3> tuple{{ramBitCast(env0[0]),ramBitCast(RamSigned(4)),ramBitCast(RamSigned(7))}};
rel_interm_out_violation_fff__bda2c2e8e8813350->insert(tuple,READ_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt));
break;
}
}
}
} catch(std::exception &e) { signalHandler->error(e.what());}
}
PARALLEL_END
}
();}
signalHandler->setMsg(R"_(@interm_out.violation.{fff}(E,"minLength","Nationality must be valid") :- 
   @magic.@interm_out.violation.{fff}(),
   person(E),
   nationality(E,V),
   strlen(V) < 1.
in file  [1:1-1:1])_");
if(!(rel_person_4b7efb71e7bbaeee->empty()) && !(rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06->empty()) && !(rel_nationality_45001e24d435ebbf->empty())) {
[&](){
auto part = rel_person_4b7efb71e7bbaeee->partition();
PARALLEL_START
CREATE_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt,rel_interm_out_violation_fff__bda2c2e8e8813350->createContext());
CREATE_OP_CONTEXT(rel_nationality_45001e24d435ebbf_op_ctxt,rel_nationality_45001e24d435ebbf->createContext());
CREATE_OP_CONTEXT(rel_person_4b7efb71e7bbaeee_op_ctxt,rel_person_4b7efb71e7bbaeee->createContext());

                   #if defined _OPENMP && _OPENMP < 200805
                           auto count = std::distance(part.begin(), part.end());
                           auto base = part.begin();
                           pfor(int index  = 0; index < count; index++) {
                               auto it = base + index;
                   #else
                           pfor(auto it = part.begin(); it < part.end(); it++) {
                   #endif
                   try{
for(const auto& env0 : *it) {
auto range = rel_nationality_45001e24d435ebbf->lowerUpperRange_10(Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MIN_RAM_SIGNED)}},Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MAX_RAM_SIGNED)}},READ_OP_CONTEXT(rel_nationality_45001e24d435ebbf_op_ctxt));
for(const auto& env1 : range) {
if( (ramBitCast<RamSigned>(static_cast<RamSigned>(symTable.decode(env1[1]).size())) < ramBitCast<RamSigned>(RamSigned(1)))) {
Tuple<RamDomain,3> tuple{{ramBitCast(env0[0]),ramBitCast(RamSigned(3)),ramBitCast(RamSigned(8))}};
rel_interm_out_violation_fff__bda2c2e8e8813350->insert(tuple,READ_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt));
break;
}
}
}
} catch(std::exception &e) { signalHandler->error(e.what());}
}
PARALLEL_END
}
();}
signalHandler->setMsg(R"_(@interm_out.violation.{fff}(E,"maxLength","Nationality must be valid") :- 
   @magic.@interm_out.violation.{fff}(),
   person(E),
   nationality(E,V),
   strlen(V) > 200.
in file  [1:1-1:1])_");
if(!(rel_person_4b7efb71e7bbaeee->empty()) && !(rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06->empty()) && !(rel_nationality_45001e24d435ebbf->empty())) {
[&](){
auto part = rel_person_4b7efb71e7bbaeee->partition();
PARALLEL_START
CREATE_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt,rel_interm_out_violation_fff__bda2c2e8e8813350->createContext());
CREATE_OP_CONTEXT(rel_nationality_45001e24d435ebbf_op_ctxt,rel_nationality_45001e24d435ebbf->createContext());
CREATE_OP_CONTEXT(rel_person_4b7efb71e7bbaeee_op_ctxt,rel_person_4b7efb71e7bbaeee->createContext());

                   #if defined _OPENMP && _OPENMP < 200805
                           auto count = std::distance(part.begin(), part.end());
                           auto base = part.begin();
                           pfor(int index  = 0; index < count; index++) {
                               auto it = base + index;
                   #else
                           pfor(auto it = part.begin(); it < part.end(); it++) {
                   #endif
                   try{
for(const auto& env0 : *it) {
auto range = rel_nationality_45001e24d435ebbf->lowerUpperRange_10(Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MIN_RAM_SIGNED)}},Tuple<RamDomain,2>{{ramBitCast(env0[0]), ramBitCast<RamDomain>(MAX_RAM_SIGNED)}},READ_OP_CONTEXT(rel_nationality_45001e24d435ebbf_op_ctxt));
for(const auto& env1 : range) {
if( (ramBitCast<RamSigned>(static_cast<RamSigned>(symTable.decode(env1[1]).size())) > ramBitCast<RamSigned>(RamSigned(200)))) {
Tuple<RamDomain,3> tuple{{ramBitCast(env0[0]),ramBitCast(RamSigned(4)),ramBitCast(RamSigned(8))}};
rel_interm_out_violation_fff__bda2c2e8e8813350->insert(tuple,READ_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt));
break;
}
}
}
} catch(std::exception &e) { signalHandler->error(e.what());}
}
PARALLEL_END
}
();}
rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06->purge();
rel_neglabel_has_name_be2950f430dab32a->purge();
rel_neglabel_has_occupation_f0e827e7bbd5a7f2->purge();
if (pruneImdtRels) rel_birthDate_9bc1888ef26605d0->purge();
if (pruneImdtRels) rel_deathDate_2a1e0db35f240968->purge();
if (pruneImdtRels) rel_name_58440f57e1b2dd1f->purge();
if (pruneImdtRels) rel_nationality_45001e24d435ebbf->purge();
if (pruneImdtRels) rel_occupation_76c3c68cff8238ec->purge();
if (pruneImdtRels) rel_person_4b7efb71e7bbaeee->purge();
}

} // namespace  souffle

namespace  souffle {
using namespace souffle;
class Stratum_magic_interm_out_violation_fff__d73f256a9c9a6d88 {
public:
 Stratum_magic_interm_out_violation_fff__d73f256a9c9a6d88(SymbolTable& symTable,RecordTable& recordTable,ConcurrentCache<std::string,std::regex>& regexCache,bool& pruneImdtRels,bool& performIO,SignalHandler*& signalHandler,std::atomic<std::size_t>& iter,std::atomic<RamDomain>& ctr,std::string& inputDirectory,std::string& outputDirectory,t_nullaries& rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06);
void run([[maybe_unused]] const std::vector<RamDomain>& args,[[maybe_unused]] std::vector<RamDomain>& ret);
private:
SymbolTable& symTable;
RecordTable& recordTable;
ConcurrentCache<std::string,std::regex>& regexCache;
bool& pruneImdtRels;
bool& performIO;
SignalHandler*& signalHandler;
std::atomic<std::size_t>& iter;
std::atomic<RamDomain>& ctr;
std::string& inputDirectory;
std::string& outputDirectory;
t_nullaries* rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06;
};
} // namespace  souffle
namespace  souffle {
using namespace souffle;
 Stratum_magic_interm_out_violation_fff__d73f256a9c9a6d88::Stratum_magic_interm_out_violation_fff__d73f256a9c9a6d88(SymbolTable& symTable,RecordTable& recordTable,ConcurrentCache<std::string,std::regex>& regexCache,bool& pruneImdtRels,bool& performIO,SignalHandler*& signalHandler,std::atomic<std::size_t>& iter,std::atomic<RamDomain>& ctr,std::string& inputDirectory,std::string& outputDirectory,t_nullaries& rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06):
symTable(symTable),
recordTable(recordTable),
regexCache(regexCache),
pruneImdtRels(pruneImdtRels),
performIO(performIO),
signalHandler(signalHandler),
iter(iter),
ctr(ctr),
inputDirectory(inputDirectory),
outputDirectory(outputDirectory),
rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06(&rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06){
}

void Stratum_magic_interm_out_violation_fff__d73f256a9c9a6d88::run([[maybe_unused]] const std::vector<RamDomain>& args,[[maybe_unused]] std::vector<RamDomain>& ret){
signalHandler->setMsg(R"_(@magic.@interm_out.violation.{fff}().
in file  [1:1-1:1])_");
if(rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06->empty()) {
[&](){
CREATE_OP_CONTEXT(rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06_op_ctxt,rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06->createContext());
Tuple<RamDomain,0> tuple{{}};
rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06->insert(tuple,READ_OP_CONTEXT(rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06_op_ctxt));
}
();}
}

} // namespace  souffle

namespace  souffle {
using namespace souffle;
class Stratum_neglabel_has_name_5d1b2e422926ace9 {
public:
 Stratum_neglabel_has_name_5d1b2e422926ace9(SymbolTable& symTable,RecordTable& recordTable,ConcurrentCache<std::string,std::regex>& regexCache,bool& pruneImdtRels,bool& performIO,SignalHandler*& signalHandler,std::atomic<std::size_t>& iter,std::atomic<RamDomain>& ctr,std::string& inputDirectory,std::string& outputDirectory,t_btree_000_i__0__1::Type& rel_neglabel_has_name_be2950f430dab32a,t_btree_000_ii__0_1__11__10::Type& rel_name_58440f57e1b2dd1f);
void run([[maybe_unused]] const std::vector<RamDomain>& args,[[maybe_unused]] std::vector<RamDomain>& ret);
private:
SymbolTable& symTable;
RecordTable& recordTable;
ConcurrentCache<std::string,std::regex>& regexCache;
bool& pruneImdtRels;
bool& performIO;
SignalHandler*& signalHandler;
std::atomic<std::size_t>& iter;
std::atomic<RamDomain>& ctr;
std::string& inputDirectory;
std::string& outputDirectory;
t_btree_000_i__0__1::Type* rel_neglabel_has_name_be2950f430dab32a;
t_btree_000_ii__0_1__11__10::Type* rel_name_58440f57e1b2dd1f;
};
} // namespace  souffle
namespace  souffle {
using namespace souffle;
 Stratum_neglabel_has_name_5d1b2e422926ace9::Stratum_neglabel_has_name_5d1b2e422926ace9(SymbolTable& symTable,RecordTable& recordTable,ConcurrentCache<std::string,std::regex>& regexCache,bool& pruneImdtRels,bool& performIO,SignalHandler*& signalHandler,std::atomic<std::size_t>& iter,std::atomic<RamDomain>& ctr,std::string& inputDirectory,std::string& outputDirectory,t_btree_000_i__0__1::Type& rel_neglabel_has_name_be2950f430dab32a,t_btree_000_ii__0_1__11__10::Type& rel_name_58440f57e1b2dd1f):
symTable(symTable),
recordTable(recordTable),
regexCache(regexCache),
pruneImdtRels(pruneImdtRels),
performIO(performIO),
signalHandler(signalHandler),
iter(iter),
ctr(ctr),
inputDirectory(inputDirectory),
outputDirectory(outputDirectory),
rel_neglabel_has_name_be2950f430dab32a(&rel_neglabel_has_name_be2950f430dab32a),
rel_name_58440f57e1b2dd1f(&rel_name_58440f57e1b2dd1f){
}

void Stratum_neglabel_has_name_5d1b2e422926ace9::run([[maybe_unused]] const std::vector<RamDomain>& args,[[maybe_unused]] std::vector<RamDomain>& ret){
signalHandler->setMsg(R"_(@neglabel.has_name(E) :- 
   name(E,_).
in file  [1:1-1:1])_");
if(!(rel_name_58440f57e1b2dd1f->empty())) {
[&](){
CREATE_OP_CONTEXT(rel_neglabel_has_name_be2950f430dab32a_op_ctxt,rel_neglabel_has_name_be2950f430dab32a->createContext());
CREATE_OP_CONTEXT(rel_name_58440f57e1b2dd1f_op_ctxt,rel_name_58440f57e1b2dd1f->createContext());
for(const auto& env0 : *rel_name_58440f57e1b2dd1f) {
Tuple<RamDomain,1> tuple{{ramBitCast(env0[0])}};
rel_neglabel_has_name_be2950f430dab32a->insert(tuple,READ_OP_CONTEXT(rel_neglabel_has_name_be2950f430dab32a_op_ctxt));
}
}
();}
}

} // namespace  souffle

namespace  souffle {
using namespace souffle;
class Stratum_neglabel_has_occupation_d147b81041d9b03e {
public:
 Stratum_neglabel_has_occupation_d147b81041d9b03e(SymbolTable& symTable,RecordTable& recordTable,ConcurrentCache<std::string,std::regex>& regexCache,bool& pruneImdtRels,bool& performIO,SignalHandler*& signalHandler,std::atomic<std::size_t>& iter,std::atomic<RamDomain>& ctr,std::string& inputDirectory,std::string& outputDirectory,t_btree_000_i__0__1::Type& rel_neglabel_has_occupation_f0e827e7bbd5a7f2,t_btree_000_ii__0_1__11__10::Type& rel_occupation_76c3c68cff8238ec);
void run([[maybe_unused]] const std::vector<RamDomain>& args,[[maybe_unused]] std::vector<RamDomain>& ret);
private:
SymbolTable& symTable;
RecordTable& recordTable;
ConcurrentCache<std::string,std::regex>& regexCache;
bool& pruneImdtRels;
bool& performIO;
SignalHandler*& signalHandler;
std::atomic<std::size_t>& iter;
std::atomic<RamDomain>& ctr;
std::string& inputDirectory;
std::string& outputDirectory;
t_btree_000_i__0__1::Type* rel_neglabel_has_occupation_f0e827e7bbd5a7f2;
t_btree_000_ii__0_1__11__10::Type* rel_occupation_76c3c68cff8238ec;
};
} // namespace  souffle
namespace  souffle {
using namespace souffle;
 Stratum_neglabel_has_occupation_d147b81041d9b03e::Stratum_neglabel_has_occupation_d147b81041d9b03e(SymbolTable& symTable,RecordTable& recordTable,ConcurrentCache<std::string,std::regex>& regexCache,bool& pruneImdtRels,bool& performIO,SignalHandler*& signalHandler,std::atomic<std::size_t>& iter,std::atomic<RamDomain>& ctr,std::string& inputDirectory,std::string& outputDirectory,t_btree_000_i__0__1::Type& rel_neglabel_has_occupation_f0e827e7bbd5a7f2,t_btree_000_ii__0_1__11__10::Type& rel_occupation_76c3c68cff8238ec):
symTable(symTable),
recordTable(recordTable),
regexCache(regexCache),
pruneImdtRels(pruneImdtRels),
performIO(performIO),
signalHandler(signalHandler),
iter(iter),
ctr(ctr),
inputDirectory(inputDirectory),
outputDirectory(outputDirectory),
rel_neglabel_has_occupation_f0e827e7bbd5a7f2(&rel_neglabel_has_occupation_f0e827e7bbd5a7f2),
rel_occupation_76c3c68cff8238ec(&rel_occupation_76c3c68cff8238ec){
}

void Stratum_neglabel_has_occupation_d147b81041d9b03e::run([[maybe_unused]] const std::vector<RamDomain>& args,[[maybe_unused]] std::vector<RamDomain>& ret){
signalHandler->setMsg(R"_(@neglabel.has_occupation(E) :- 
   occupation(E,_).
in file  [1:1-1:1])_");
if(!(rel_occupation_76c3c68cff8238ec->empty())) {
[&](){
CREATE_OP_CONTEXT(rel_neglabel_has_occupation_f0e827e7bbd5a7f2_op_ctxt,rel_neglabel_has_occupation_f0e827e7bbd5a7f2->createContext());
CREATE_OP_CONTEXT(rel_occupation_76c3c68cff8238ec_op_ctxt,rel_occupation_76c3c68cff8238ec->createContext());
for(const auto& env0 : *rel_occupation_76c3c68cff8238ec) {
Tuple<RamDomain,1> tuple{{ramBitCast(env0[0])}};
rel_neglabel_has_occupation_f0e827e7bbd5a7f2->insert(tuple,READ_OP_CONTEXT(rel_neglabel_has_occupation_f0e827e7bbd5a7f2_op_ctxt));
}
}
();}
}

} // namespace  souffle

namespace  souffle {
using namespace souffle;
class Stratum_birthDate_a088d5339d860f10 {
public:
 Stratum_birthDate_a088d5339d860f10(SymbolTable& symTable,RecordTable& recordTable,ConcurrentCache<std::string,std::regex>& regexCache,bool& pruneImdtRels,bool& performIO,SignalHandler*& signalHandler,std::atomic<std::size_t>& iter,std::atomic<RamDomain>& ctr,std::string& inputDirectory,std::string& outputDirectory,t_btree_000_ii__0_1__11__10::Type& rel_birthDate_9bc1888ef26605d0);
void run([[maybe_unused]] const std::vector<RamDomain>& args,[[maybe_unused]] std::vector<RamDomain>& ret);
private:
SymbolTable& symTable;
RecordTable& recordTable;
ConcurrentCache<std::string,std::regex>& regexCache;
bool& pruneImdtRels;
bool& performIO;
SignalHandler*& signalHandler;
std::atomic<std::size_t>& iter;
std::atomic<RamDomain>& ctr;
std::string& inputDirectory;
std::string& outputDirectory;
t_btree_000_ii__0_1__11__10::Type* rel_birthDate_9bc1888ef26605d0;
};
} // namespace  souffle
namespace  souffle {
using namespace souffle;
 Stratum_birthDate_a088d5339d860f10::Stratum_birthDate_a088d5339d860f10(SymbolTable& symTable,RecordTable& recordTable,ConcurrentCache<std::string,std::regex>& regexCache,bool& pruneImdtRels,bool& performIO,SignalHandler*& signalHandler,std::atomic<std::size_t>& iter,std::atomic<RamDomain>& ctr,std::string& inputDirectory,std::string& outputDirectory,t_btree_000_ii__0_1__11__10::Type& rel_birthDate_9bc1888ef26605d0):
symTable(symTable),
recordTable(recordTable),
regexCache(regexCache),
pruneImdtRels(pruneImdtRels),
performIO(performIO),
signalHandler(signalHandler),
iter(iter),
ctr(ctr),
inputDirectory(inputDirectory),
outputDirectory(outputDirectory),
rel_birthDate_9bc1888ef26605d0(&rel_birthDate_9bc1888ef26605d0){
}

void Stratum_birthDate_a088d5339d860f10::run([[maybe_unused]] const std::vector<RamDomain>& args,[[maybe_unused]] std::vector<RamDomain>& ret){
if (performIO) {
try {std::map<std::string, std::string> directiveMap({{R"_(IO)_",R"_(file)_"},{R"_(attributeNames)_",R"_(entity	value)_"},{R"_(auxArity)_",R"_(0)_"},{R"_(fact-dir)_",R"_(results/facts)_"},{R"_(name)_",R"_(birthDate)_"},{R"_(operation)_",R"_(input)_"},{R"_(params)_",R"_({"records": {}, "relation": {"arity": 2, "params": ["entity", "value"]}})_"},{R"_(types)_",R"_({"ADTs": {}, "records": {}, "relation": {"arity": 2, "types": ["s:symbol", "s:symbol"]}})_"}});
if (!inputDirectory.empty()) {directiveMap["fact-dir"] = inputDirectory;}
IOSystem::getInstance().getReader(directiveMap, symTable, recordTable)->readAll(*rel_birthDate_9bc1888ef26605d0);
} catch (std::exception& e) {std::cerr << "Error loading birthDate data: " << e.what() << '\n';
exit(1);
}
}
}

} // namespace  souffle

namespace  souffle {
using namespace souffle;
class Stratum_deathDate_b8dab8d7f58db172 {
public:
 Stratum_deathDate_b8dab8d7f58db172(SymbolTable& symTable,RecordTable& recordTable,ConcurrentCache<std::string,std::regex>& regexCache,bool& pruneImdtRels,bool& performIO,SignalHandler*& signalHandler,std::atomic<std::size_t>& iter,std::atomic<RamDomain>& ctr,std::string& inputDirectory,std::string& outputDirectory,t_btree_000_ii__0_1__11__10::Type& rel_deathDate_2a1e0db35f240968);
void run([[maybe_unused]] const std::vector<RamDomain>& args,[[maybe_unused]] std::vector<RamDomain>& ret);
private:
SymbolTable& symTable;
RecordTable& recordTable;
ConcurrentCache<std::string,std::regex>& regexCache;
bool& pruneImdtRels;
bool& performIO;
SignalHandler*& signalHandler;
std::atomic<std::size_t>& iter;
std::atomic<RamDomain>& ctr;
std::string& inputDirectory;
std::string& outputDirectory;
t_btree_000_ii__0_1__11__10::Type* rel_deathDate_2a1e0db35f240968;
};
} // namespace  souffle
namespace  souffle {
using namespace souffle;
 Stratum_deathDate_b8dab8d7f58db172::Stratum_deathDate_b8dab8d7f58db172(SymbolTable& symTable,RecordTable& recordTable,ConcurrentCache<std::string,std::regex>& regexCache,bool& pruneImdtRels,bool& performIO,SignalHandler*& signalHandler,std::atomic<std::size_t>& iter,std::atomic<RamDomain>& ctr,std::string& inputDirectory,std::string& outputDirectory,t_btree_000_ii__0_1__11__10::Type& rel_deathDate_2a1e0db35f240968):
symTable(symTable),
recordTable(recordTable),
regexCache(regexCache),
pruneImdtRels(pruneImdtRels),
performIO(performIO),
signalHandler(signalHandler),
iter(iter),
ctr(ctr),
inputDirectory(inputDirectory),
outputDirectory(outputDirectory),
rel_deathDate_2a1e0db35f240968(&rel_deathDate_2a1e0db35f240968){
}

void Stratum_deathDate_b8dab8d7f58db172::run([[maybe_unused]] const std::vector<RamDomain>& args,[[maybe_unused]] std::vector<RamDomain>& ret){
if (performIO) {
try {std::map<std::string, std::string> directiveMap({{R"_(IO)_",R"_(file)_"},{R"_(attributeNames)_",R"_(entity	value)_"},{R"_(auxArity)_",R"_(0)_"},{R"_(fact-dir)_",R"_(results/facts)_"},{R"_(name)_",R"_(deathDate)_"},{R"_(operation)_",R"_(input)_"},{R"_(params)_",R"_({"records": {}, "relation": {"arity": 2, "params": ["entity", "value"]}})_"},{R"_(types)_",R"_({"ADTs": {}, "records": {}, "relation": {"arity": 2, "types": ["s:symbol", "s:symbol"]}})_"}});
if (!inputDirectory.empty()) {directiveMap["fact-dir"] = inputDirectory;}
IOSystem::getInstance().getReader(directiveMap, symTable, recordTable)->readAll(*rel_deathDate_2a1e0db35f240968);
} catch (std::exception& e) {std::cerr << "Error loading deathDate data: " << e.what() << '\n';
exit(1);
}
}
}

} // namespace  souffle

namespace  souffle {
using namespace souffle;
class Stratum_name_138c7e696dc67916 {
public:
 Stratum_name_138c7e696dc67916(SymbolTable& symTable,RecordTable& recordTable,ConcurrentCache<std::string,std::regex>& regexCache,bool& pruneImdtRels,bool& performIO,SignalHandler*& signalHandler,std::atomic<std::size_t>& iter,std::atomic<RamDomain>& ctr,std::string& inputDirectory,std::string& outputDirectory,t_btree_000_ii__0_1__11__10::Type& rel_name_58440f57e1b2dd1f);
void run([[maybe_unused]] const std::vector<RamDomain>& args,[[maybe_unused]] std::vector<RamDomain>& ret);
private:
SymbolTable& symTable;
RecordTable& recordTable;
ConcurrentCache<std::string,std::regex>& regexCache;
bool& pruneImdtRels;
bool& performIO;
SignalHandler*& signalHandler;
std::atomic<std::size_t>& iter;
std::atomic<RamDomain>& ctr;
std::string& inputDirectory;
std::string& outputDirectory;
t_btree_000_ii__0_1__11__10::Type* rel_name_58440f57e1b2dd1f;
};
} // namespace  souffle
namespace  souffle {
using namespace souffle;
 Stratum_name_138c7e696dc67916::Stratum_name_138c7e696dc67916(SymbolTable& symTable,RecordTable& recordTable,ConcurrentCache<std::string,std::regex>& regexCache,bool& pruneImdtRels,bool& performIO,SignalHandler*& signalHandler,std::atomic<std::size_t>& iter,std::atomic<RamDomain>& ctr,std::string& inputDirectory,std::string& outputDirectory,t_btree_000_ii__0_1__11__10::Type& rel_name_58440f57e1b2dd1f):
symTable(symTable),
recordTable(recordTable),
regexCache(regexCache),
pruneImdtRels(pruneImdtRels),
performIO(performIO),
signalHandler(signalHandler),
iter(iter),
ctr(ctr),
inputDirectory(inputDirectory),
outputDirectory(outputDirectory),
rel_name_58440f57e1b2dd1f(&rel_name_58440f57e1b2dd1f){
}

void Stratum_name_138c7e696dc67916::run([[maybe_unused]] const std::vector<RamDomain>& args,[[maybe_unused]] std::vector<RamDomain>& ret){
if (performIO) {
try {std::map<std::string, std::string> directiveMap({{R"_(IO)_",R"_(file)_"},{R"_(attributeNames)_",R"_(entity	value)_"},{R"_(auxArity)_",R"_(0)_"},{R"_(fact-dir)_",R"_(results/facts)_"},{R"_(name)_",R"_(name)_"},{R"_(operation)_",R"_(input)_"},{R"_(params)_",R"_({"records": {}, "relation": {"arity": 2, "params": ["entity", "value"]}})_"},{R"_(types)_",R"_({"ADTs": {}, "records": {}, "relation": {"arity": 2, "types": ["s:symbol", "s:symbol"]}})_"}});
if (!inputDirectory.empty()) {directiveMap["fact-dir"] = inputDirectory;}
IOSystem::getInstance().getReader(directiveMap, symTable, recordTable)->readAll(*rel_name_58440f57e1b2dd1f);
} catch (std::exception& e) {std::cerr << "Error loading name data: " << e.what() << '\n';
exit(1);
}
}
}

} // namespace  souffle

namespace  souffle {
using namespace souffle;
class Stratum_nationality_67bd28f4d80f64ce {
public:
 Stratum_nationality_67bd28f4d80f64ce(SymbolTable& symTable,RecordTable& recordTable,ConcurrentCache<std::string,std::regex>& regexCache,bool& pruneImdtRels,bool& performIO,SignalHandler*& signalHandler,std::atomic<std::size_t>& iter,std::atomic<RamDomain>& ctr,std::string& inputDirectory,std::string& outputDirectory,t_btree_000_ii__0_1__11__10::Type& rel_nationality_45001e24d435ebbf);
void run([[maybe_unused]] const std::vector<RamDomain>& args,[[maybe_unused]] std::vector<RamDomain>& ret);
private:
SymbolTable& symTable;
RecordTable& recordTable;
ConcurrentCache<std::string,std::regex>& regexCache;
bool& pruneImdtRels;
bool& performIO;
SignalHandler*& signalHandler;
std::atomic<std::size_t>& iter;
std::atomic<RamDomain>& ctr;
std::string& inputDirectory;
std::string& outputDirectory;
t_btree_000_ii__0_1__11__10::Type* rel_nationality_45001e24d435ebbf;
};
} // namespace  souffle
namespace  souffle {
using namespace souffle;
 Stratum_nationality_67bd28f4d80f64ce::Stratum_nationality_67bd28f4d80f64ce(SymbolTable& symTable,RecordTable& recordTable,ConcurrentCache<std::string,std::regex>& regexCache,bool& pruneImdtRels,bool& performIO,SignalHandler*& signalHandler,std::atomic<std::size_t>& iter,std::atomic<RamDomain>& ctr,std::string& inputDirectory,std::string& outputDirectory,t_btree_000_ii__0_1__11__10::Type& rel_nationality_45001e24d435ebbf):
symTable(symTable),
recordTable(recordTable),
regexCache(regexCache),
pruneImdtRels(pruneImdtRels),
performIO(performIO),
signalHandler(signalHandler),
iter(iter),
ctr(ctr),
inputDirectory(inputDirectory),
outputDirectory(outputDirectory),
rel_nationality_45001e24d435ebbf(&rel_nationality_45001e24d435ebbf){
}

void Stratum_nationality_67bd28f4d80f64ce::run([[maybe_unused]] const std::vector<RamDomain>& args,[[maybe_unused]] std::vector<RamDomain>& ret){
if (performIO) {
try {std::map<std::string, std::string> directiveMap({{R"_(IO)_",R"_(file)_"},{R"_(attributeNames)_",R"_(entity	value)_"},{R"_(auxArity)_",R"_(0)_"},{R"_(fact-dir)_",R"_(results/facts)_"},{R"_(name)_",R"_(nationality)_"},{R"_(operation)_",R"_(input)_"},{R"_(params)_",R"_({"records": {}, "relation": {"arity": 2, "params": ["entity", "value"]}})_"},{R"_(types)_",R"_({"ADTs": {}, "records": {}, "relation": {"arity": 2, "types": ["s:symbol", "s:symbol"]}})_"}});
if (!inputDirectory.empty()) {directiveMap["fact-dir"] = inputDirectory;}
IOSystem::getInstance().getReader(directiveMap, symTable, recordTable)->readAll(*rel_nationality_45001e24d435ebbf);
} catch (std::exception& e) {std::cerr << "Error loading nationality data: " << e.what() << '\n';
exit(1);
}
}
}

} // namespace  souffle

namespace  souffle {
using namespace souffle;
class Stratum_occupation_3c8ffe3332538589 {
public:
 Stratum_occupation_3c8ffe3332538589(SymbolTable& symTable,RecordTable& recordTable,ConcurrentCache<std::string,std::regex>& regexCache,bool& pruneImdtRels,bool& performIO,SignalHandler*& signalHandler,std::atomic<std::size_t>& iter,std::atomic<RamDomain>& ctr,std::string& inputDirectory,std::string& outputDirectory,t_btree_000_ii__0_1__11__10::Type& rel_occupation_76c3c68cff8238ec);
void run([[maybe_unused]] const std::vector<RamDomain>& args,[[maybe_unused]] std::vector<RamDomain>& ret);
private:
SymbolTable& symTable;
RecordTable& recordTable;
ConcurrentCache<std::string,std::regex>& regexCache;
bool& pruneImdtRels;
bool& performIO;
SignalHandler*& signalHandler;
std::atomic<std::size_t>& iter;
std::atomic<RamDomain>& ctr;
std::string& inputDirectory;
std::string& outputDirectory;
t_btree_000_ii__0_1__11__10::Type* rel_occupation_76c3c68cff8238ec;
};
} // namespace  souffle
namespace  souffle {
using namespace souffle;
 Stratum_occupation_3c8ffe3332538589::Stratum_occupation_3c8ffe3332538589(SymbolTable& symTable,RecordTable& recordTable,ConcurrentCache<std::string,std::regex>& regexCache,bool& pruneImdtRels,bool& performIO,SignalHandler*& signalHandler,std::atomic<std::size_t>& iter,std::atomic<RamDomain>& ctr,std::string& inputDirectory,std::string& outputDirectory,t_btree_000_ii__0_1__11__10::Type& rel_occupation_76c3c68cff8238ec):
symTable(symTable),
recordTable(recordTable),
regexCache(regexCache),
pruneImdtRels(pruneImdtRels),
performIO(performIO),
signalHandler(signalHandler),
iter(iter),
ctr(ctr),
inputDirectory(inputDirectory),
outputDirectory(outputDirectory),
rel_occupation_76c3c68cff8238ec(&rel_occupation_76c3c68cff8238ec){
}

void Stratum_occupation_3c8ffe3332538589::run([[maybe_unused]] const std::vector<RamDomain>& args,[[maybe_unused]] std::vector<RamDomain>& ret){
if (performIO) {
try {std::map<std::string, std::string> directiveMap({{R"_(IO)_",R"_(file)_"},{R"_(attributeNames)_",R"_(entity	value)_"},{R"_(auxArity)_",R"_(0)_"},{R"_(fact-dir)_",R"_(results/facts)_"},{R"_(name)_",R"_(occupation)_"},{R"_(operation)_",R"_(input)_"},{R"_(params)_",R"_({"records": {}, "relation": {"arity": 2, "params": ["entity", "value"]}})_"},{R"_(types)_",R"_({"ADTs": {}, "records": {}, "relation": {"arity": 2, "types": ["s:symbol", "s:symbol"]}})_"}});
if (!inputDirectory.empty()) {directiveMap["fact-dir"] = inputDirectory;}
IOSystem::getInstance().getReader(directiveMap, symTable, recordTable)->readAll(*rel_occupation_76c3c68cff8238ec);
} catch (std::exception& e) {std::cerr << "Error loading occupation data: " << e.what() << '\n';
exit(1);
}
}
}

} // namespace  souffle

namespace  souffle {
using namespace souffle;
class Stratum_person_532be01e7fa33dcd {
public:
 Stratum_person_532be01e7fa33dcd(SymbolTable& symTable,RecordTable& recordTable,ConcurrentCache<std::string,std::regex>& regexCache,bool& pruneImdtRels,bool& performIO,SignalHandler*& signalHandler,std::atomic<std::size_t>& iter,std::atomic<RamDomain>& ctr,std::string& inputDirectory,std::string& outputDirectory,t_btree_000_i__0__1::Type& rel_person_4b7efb71e7bbaeee);
void run([[maybe_unused]] const std::vector<RamDomain>& args,[[maybe_unused]] std::vector<RamDomain>& ret);
private:
SymbolTable& symTable;
RecordTable& recordTable;
ConcurrentCache<std::string,std::regex>& regexCache;
bool& pruneImdtRels;
bool& performIO;
SignalHandler*& signalHandler;
std::atomic<std::size_t>& iter;
std::atomic<RamDomain>& ctr;
std::string& inputDirectory;
std::string& outputDirectory;
t_btree_000_i__0__1::Type* rel_person_4b7efb71e7bbaeee;
};
} // namespace  souffle
namespace  souffle {
using namespace souffle;
 Stratum_person_532be01e7fa33dcd::Stratum_person_532be01e7fa33dcd(SymbolTable& symTable,RecordTable& recordTable,ConcurrentCache<std::string,std::regex>& regexCache,bool& pruneImdtRels,bool& performIO,SignalHandler*& signalHandler,std::atomic<std::size_t>& iter,std::atomic<RamDomain>& ctr,std::string& inputDirectory,std::string& outputDirectory,t_btree_000_i__0__1::Type& rel_person_4b7efb71e7bbaeee):
symTable(symTable),
recordTable(recordTable),
regexCache(regexCache),
pruneImdtRels(pruneImdtRels),
performIO(performIO),
signalHandler(signalHandler),
iter(iter),
ctr(ctr),
inputDirectory(inputDirectory),
outputDirectory(outputDirectory),
rel_person_4b7efb71e7bbaeee(&rel_person_4b7efb71e7bbaeee){
}

void Stratum_person_532be01e7fa33dcd::run([[maybe_unused]] const std::vector<RamDomain>& args,[[maybe_unused]] std::vector<RamDomain>& ret){
if (performIO) {
try {std::map<std::string, std::string> directiveMap({{R"_(IO)_",R"_(file)_"},{R"_(attributeNames)_",R"_(entity)_"},{R"_(auxArity)_",R"_(0)_"},{R"_(fact-dir)_",R"_(results/facts)_"},{R"_(name)_",R"_(person)_"},{R"_(operation)_",R"_(input)_"},{R"_(params)_",R"_({"records": {}, "relation": {"arity": 1, "params": ["entity"]}})_"},{R"_(types)_",R"_({"ADTs": {}, "records": {}, "relation": {"arity": 1, "types": ["s:symbol"]}})_"}});
if (!inputDirectory.empty()) {directiveMap["fact-dir"] = inputDirectory;}
IOSystem::getInstance().getReader(directiveMap, symTable, recordTable)->readAll(*rel_person_4b7efb71e7bbaeee);
} catch (std::exception& e) {std::cerr << "Error loading person data: " << e.what() << '\n';
exit(1);
}
}
}

} // namespace  souffle

namespace  souffle {
using namespace souffle;
class Stratum_violation_f648bb2709de2cd8 {
public:
 Stratum_violation_f648bb2709de2cd8(SymbolTable& symTable,RecordTable& recordTable,ConcurrentCache<std::string,std::regex>& regexCache,bool& pruneImdtRels,bool& performIO,SignalHandler*& signalHandler,std::atomic<std::size_t>& iter,std::atomic<RamDomain>& ctr,std::string& inputDirectory,std::string& outputDirectory,t_btree_000_iii__0_1_2__111::Type& rel_interm_out_violation_fff__bda2c2e8e8813350,t_btree_000_iii__0_1_2__111::Type& rel_violation_0e1a24bba958dc61);
void run([[maybe_unused]] const std::vector<RamDomain>& args,[[maybe_unused]] std::vector<RamDomain>& ret);
private:
SymbolTable& symTable;
RecordTable& recordTable;
ConcurrentCache<std::string,std::regex>& regexCache;
bool& pruneImdtRels;
bool& performIO;
SignalHandler*& signalHandler;
std::atomic<std::size_t>& iter;
std::atomic<RamDomain>& ctr;
std::string& inputDirectory;
std::string& outputDirectory;
t_btree_000_iii__0_1_2__111::Type* rel_interm_out_violation_fff__bda2c2e8e8813350;
t_btree_000_iii__0_1_2__111::Type* rel_violation_0e1a24bba958dc61;
};
} // namespace  souffle
namespace  souffle {
using namespace souffle;
 Stratum_violation_f648bb2709de2cd8::Stratum_violation_f648bb2709de2cd8(SymbolTable& symTable,RecordTable& recordTable,ConcurrentCache<std::string,std::regex>& regexCache,bool& pruneImdtRels,bool& performIO,SignalHandler*& signalHandler,std::atomic<std::size_t>& iter,std::atomic<RamDomain>& ctr,std::string& inputDirectory,std::string& outputDirectory,t_btree_000_iii__0_1_2__111::Type& rel_interm_out_violation_fff__bda2c2e8e8813350,t_btree_000_iii__0_1_2__111::Type& rel_violation_0e1a24bba958dc61):
symTable(symTable),
recordTable(recordTable),
regexCache(regexCache),
pruneImdtRels(pruneImdtRels),
performIO(performIO),
signalHandler(signalHandler),
iter(iter),
ctr(ctr),
inputDirectory(inputDirectory),
outputDirectory(outputDirectory),
rel_interm_out_violation_fff__bda2c2e8e8813350(&rel_interm_out_violation_fff__bda2c2e8e8813350),
rel_violation_0e1a24bba958dc61(&rel_violation_0e1a24bba958dc61){
}

void Stratum_violation_f648bb2709de2cd8::run([[maybe_unused]] const std::vector<RamDomain>& args,[[maybe_unused]] std::vector<RamDomain>& ret){
signalHandler->setMsg(R"_(violation(@query_x0,@query_x1,@query_x2) :- 
   @interm_out.violation.{fff}(@query_x0,@query_x1,@query_x2).
in file  [1:1-1:1])_");
if(!(rel_interm_out_violation_fff__bda2c2e8e8813350->empty())) {
[&](){
CREATE_OP_CONTEXT(rel_interm_out_violation_fff__bda2c2e8e8813350_op_ctxt,rel_interm_out_violation_fff__bda2c2e8e8813350->createContext());
CREATE_OP_CONTEXT(rel_violation_0e1a24bba958dc61_op_ctxt,rel_violation_0e1a24bba958dc61->createContext());
for(const auto& env0 : *rel_interm_out_violation_fff__bda2c2e8e8813350) {
Tuple<RamDomain,3> tuple{{ramBitCast(env0[0]),ramBitCast(env0[1]),ramBitCast(env0[2])}};
rel_violation_0e1a24bba958dc61->insert(tuple,READ_OP_CONTEXT(rel_violation_0e1a24bba958dc61_op_ctxt));
}
}
();}
if (performIO) {
try {std::map<std::string, std::string> directiveMap({{R"_(IO)_",R"_(file)_"},{R"_(attributeNames)_",R"_(entity	constraint	message)_"},{R"_(auxArity)_",R"_(0)_"},{R"_(name)_",R"_(violation)_"},{R"_(operation)_",R"_(output)_"},{R"_(output-dir)_",R"_(results)_"},{R"_(params)_",R"_({"records": {}, "relation": {"arity": 3, "params": ["entity", "constraint", "message"]}})_"},{R"_(types)_",R"_({"ADTs": {}, "records": {}, "relation": {"arity": 3, "types": ["s:symbol", "s:symbol", "s:symbol"]}})_"}});
if (outputDirectory == "-"){directiveMap["IO"] = "stdout"; directiveMap["headers"] = "true";}
else if (!outputDirectory.empty()) {directiveMap["output-dir"] = outputDirectory;}
IOSystem::getInstance().getWriter(directiveMap, symTable, recordTable)->writeAll(*rel_violation_0e1a24bba958dc61);
} catch (std::exception& e) {std::cerr << e.what();exit(1);}
}
rel_interm_out_violation_fff__bda2c2e8e8813350->purge();
}

} // namespace  souffle

namespace  souffle {
using namespace souffle;
class Sf_souffle6zZFsH: public SouffleProgram {
public:
 Sf_souffle6zZFsH();
 ~Sf_souffle6zZFsH();
void run();
void runAll(std::string inputDirectoryArg = "",std::string outputDirectoryArg = "",bool performIOArg = true,bool pruneImdtRelsArg = true);
void printAll([[maybe_unused]] std::string outputDirectoryArg = "");
void loadAll([[maybe_unused]] std::string inputDirectoryArg = "");
void dumpInputs();
void dumpOutputs();
SymbolTable& getSymbolTable();
RecordTable& getRecordTable();
void setNumThreads(std::size_t numThreadsValue);
void executeSubroutine(std::string name,const std::vector<RamDomain>& args,std::vector<RamDomain>& ret);
private:
void runFunction(std::string inputDirectoryArg,std::string outputDirectoryArg,bool performIOArg,bool pruneImdtRelsArg);
SymbolTableImpl symTable;
SpecializedRecordTable<0> recordTable;
ConcurrentCache<std::string,std::regex> regexCache;
Own<t_nullaries> rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06;
Own<t_btree_000_ii__0_1__11__10::Type> rel_birthDate_9bc1888ef26605d0;
souffle::RelationWrapper<t_btree_000_ii__0_1__11__10::Type> wrapper_rel_birthDate_9bc1888ef26605d0;
Own<t_btree_000_ii__0_1__11__10::Type> rel_deathDate_2a1e0db35f240968;
souffle::RelationWrapper<t_btree_000_ii__0_1__11__10::Type> wrapper_rel_deathDate_2a1e0db35f240968;
Own<t_btree_000_ii__0_1__11__10::Type> rel_name_58440f57e1b2dd1f;
souffle::RelationWrapper<t_btree_000_ii__0_1__11__10::Type> wrapper_rel_name_58440f57e1b2dd1f;
Own<t_btree_000_ii__0_1__11__10::Type> rel_nationality_45001e24d435ebbf;
souffle::RelationWrapper<t_btree_000_ii__0_1__11__10::Type> wrapper_rel_nationality_45001e24d435ebbf;
Own<t_btree_000_ii__0_1__11__10::Type> rel_occupation_76c3c68cff8238ec;
souffle::RelationWrapper<t_btree_000_ii__0_1__11__10::Type> wrapper_rel_occupation_76c3c68cff8238ec;
Own<t_btree_000_i__0__1::Type> rel_person_4b7efb71e7bbaeee;
souffle::RelationWrapper<t_btree_000_i__0__1::Type> wrapper_rel_person_4b7efb71e7bbaeee;
Own<t_btree_000_i__0__1::Type> rel_neglabel_has_name_be2950f430dab32a;
Own<t_btree_000_i__0__1::Type> rel_neglabel_has_occupation_f0e827e7bbd5a7f2;
Own<t_btree_000_iii__0_1_2__111::Type> rel_interm_out_violation_fff__bda2c2e8e8813350;
Own<t_btree_000_iii__0_1_2__111::Type> rel_violation_0e1a24bba958dc61;
souffle::RelationWrapper<t_btree_000_iii__0_1_2__111::Type> wrapper_rel_violation_0e1a24bba958dc61;
Stratum_interm_out_violation_fff__1031d5952eeac068 stratum_interm_out_violation_fff__ba10257fdd44e5f2;
Stratum_magic_interm_out_violation_fff__d73f256a9c9a6d88 stratum_magic_interm_out_violation_fff__37ba94fccd4ef939;
Stratum_neglabel_has_name_5d1b2e422926ace9 stratum_neglabel_has_name_7c7cb4359766bf2a;
Stratum_neglabel_has_occupation_d147b81041d9b03e stratum_neglabel_has_occupation_222e45352d455374;
Stratum_birthDate_a088d5339d860f10 stratum_birthDate_6c79f235432d23a3;
Stratum_deathDate_b8dab8d7f58db172 stratum_deathDate_257202275e3b218b;
Stratum_name_138c7e696dc67916 stratum_name_7086735a54cc4457;
Stratum_nationality_67bd28f4d80f64ce stratum_nationality_4dbdff6917fc0fdb;
Stratum_occupation_3c8ffe3332538589 stratum_occupation_6823ff7471901daa;
Stratum_person_532be01e7fa33dcd stratum_person_6a04f477d567ed75;
Stratum_violation_f648bb2709de2cd8 stratum_violation_667f1d69f307571b;
std::string inputDirectory;
std::string outputDirectory;
SignalHandler* signalHandler{SignalHandler::instance()};
std::atomic<RamDomain> ctr{};
std::atomic<std::size_t> iter{};
};
} // namespace  souffle
namespace  souffle {
using namespace souffle;
 Sf_souffle6zZFsH::Sf_souffle6zZFsH():
symTable({
  R"_(minCount)_",
  R"_(Person must have a valid name)_",
  R"_(maxCount)_",
  R"_(minLength)_",
  R"_(maxLength)_",
  R"_(Person must have at least one occupation)_",
  R"_(Birth date must be reasonable format)_",
  R"_(Death date must be reasonable format)_",
  R"_(Nationality must be valid)_",
}),
recordTable(),
regexCache(),
rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06(mk<t_nullaries>()),
rel_birthDate_9bc1888ef26605d0(mk<t_btree_000_ii__0_1__11__10::Type>()),
wrapper_rel_birthDate_9bc1888ef26605d0(0, *rel_birthDate_9bc1888ef26605d0, *this, "birthDate", std::array<const char *,2>{{"s:symbol","s:symbol"}}, std::array<const char *,2>{{"entity","value"}}, 0),
rel_deathDate_2a1e0db35f240968(mk<t_btree_000_ii__0_1__11__10::Type>()),
wrapper_rel_deathDate_2a1e0db35f240968(1, *rel_deathDate_2a1e0db35f240968, *this, "deathDate", std::array<const char *,2>{{"s:symbol","s:symbol"}}, std::array<const char *,2>{{"entity","value"}}, 0),
rel_name_58440f57e1b2dd1f(mk<t_btree_000_ii__0_1__11__10::Type>()),
wrapper_rel_name_58440f57e1b2dd1f(2, *rel_name_58440f57e1b2dd1f, *this, "name", std::array<const char *,2>{{"s:symbol","s:symbol"}}, std::array<const char *,2>{{"entity","value"}}, 0),
rel_nationality_45001e24d435ebbf(mk<t_btree_000_ii__0_1__11__10::Type>()),
wrapper_rel_nationality_45001e24d435ebbf(3, *rel_nationality_45001e24d435ebbf, *this, "nationality", std::array<const char *,2>{{"s:symbol","s:symbol"}}, std::array<const char *,2>{{"entity","value"}}, 0),
rel_occupation_76c3c68cff8238ec(mk<t_btree_000_ii__0_1__11__10::Type>()),
wrapper_rel_occupation_76c3c68cff8238ec(4, *rel_occupation_76c3c68cff8238ec, *this, "occupation", std::array<const char *,2>{{"s:symbol","s:symbol"}}, std::array<const char *,2>{{"entity","value"}}, 0),
rel_person_4b7efb71e7bbaeee(mk<t_btree_000_i__0__1::Type>()),
wrapper_rel_person_4b7efb71e7bbaeee(5, *rel_person_4b7efb71e7bbaeee, *this, "person", std::array<const char *,1>{{"s:symbol"}}, std::array<const char *,1>{{"entity"}}, 0),
rel_neglabel_has_name_be2950f430dab32a(mk<t_btree_000_i__0__1::Type>()),
rel_neglabel_has_occupation_f0e827e7bbd5a7f2(mk<t_btree_000_i__0__1::Type>()),
rel_interm_out_violation_fff__bda2c2e8e8813350(mk<t_btree_000_iii__0_1_2__111::Type>()),
rel_violation_0e1a24bba958dc61(mk<t_btree_000_iii__0_1_2__111::Type>()),
wrapper_rel_violation_0e1a24bba958dc61(6, *rel_violation_0e1a24bba958dc61, *this, "violation", std::array<const char *,3>{{"s:symbol","s:symbol","s:symbol"}}, std::array<const char *,3>{{"entity","constraint","message"}}, 0),
stratum_interm_out_violation_fff__ba10257fdd44e5f2(symTable,recordTable,regexCache,pruneImdtRels,performIO,signalHandler,iter,ctr,inputDirectory,outputDirectory,*rel_interm_out_violation_fff__bda2c2e8e8813350,*rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06,*rel_neglabel_has_name_be2950f430dab32a,*rel_neglabel_has_occupation_f0e827e7bbd5a7f2,*rel_birthDate_9bc1888ef26605d0,*rel_deathDate_2a1e0db35f240968,*rel_name_58440f57e1b2dd1f,*rel_nationality_45001e24d435ebbf,*rel_occupation_76c3c68cff8238ec,*rel_person_4b7efb71e7bbaeee),
stratum_magic_interm_out_violation_fff__37ba94fccd4ef939(symTable,recordTable,regexCache,pruneImdtRels,performIO,signalHandler,iter,ctr,inputDirectory,outputDirectory,*rel_magic_interm_out_violation_fff__2e6db4ec1c95aa06),
stratum_neglabel_has_name_7c7cb4359766bf2a(symTable,recordTable,regexCache,pruneImdtRels,performIO,signalHandler,iter,ctr,inputDirectory,outputDirectory,*rel_neglabel_has_name_be2950f430dab32a,*rel_name_58440f57e1b2dd1f),
stratum_neglabel_has_occupation_222e45352d455374(symTable,recordTable,regexCache,pruneImdtRels,performIO,signalHandler,iter,ctr,inputDirectory,outputDirectory,*rel_neglabel_has_occupation_f0e827e7bbd5a7f2,*rel_occupation_76c3c68cff8238ec),
stratum_birthDate_6c79f235432d23a3(symTable,recordTable,regexCache,pruneImdtRels,performIO,signalHandler,iter,ctr,inputDirectory,outputDirectory,*rel_birthDate_9bc1888ef26605d0),
stratum_deathDate_257202275e3b218b(symTable,recordTable,regexCache,pruneImdtRels,performIO,signalHandler,iter,ctr,inputDirectory,outputDirectory,*rel_deathDate_2a1e0db35f240968),
stratum_name_7086735a54cc4457(symTable,recordTable,regexCache,pruneImdtRels,performIO,signalHandler,iter,ctr,inputDirectory,outputDirectory,*rel_name_58440f57e1b2dd1f),
stratum_nationality_4dbdff6917fc0fdb(symTable,recordTable,regexCache,pruneImdtRels,performIO,signalHandler,iter,ctr,inputDirectory,outputDirectory,*rel_nationality_45001e24d435ebbf),
stratum_occupation_6823ff7471901daa(symTable,recordTable,regexCache,pruneImdtRels,performIO,signalHandler,iter,ctr,inputDirectory,outputDirectory,*rel_occupation_76c3c68cff8238ec),
stratum_person_6a04f477d567ed75(symTable,recordTable,regexCache,pruneImdtRels,performIO,signalHandler,iter,ctr,inputDirectory,outputDirectory,*rel_person_4b7efb71e7bbaeee),
stratum_violation_667f1d69f307571b(symTable,recordTable,regexCache,pruneImdtRels,performIO,signalHandler,iter,ctr,inputDirectory,outputDirectory,*rel_interm_out_violation_fff__bda2c2e8e8813350,*rel_violation_0e1a24bba958dc61){
addRelation("birthDate", wrapper_rel_birthDate_9bc1888ef26605d0, true, false);
addRelation("deathDate", wrapper_rel_deathDate_2a1e0db35f240968, true, false);
addRelation("name", wrapper_rel_name_58440f57e1b2dd1f, true, false);
addRelation("nationality", wrapper_rel_nationality_45001e24d435ebbf, true, false);
addRelation("occupation", wrapper_rel_occupation_76c3c68cff8238ec, true, false);
addRelation("person", wrapper_rel_person_4b7efb71e7bbaeee, true, false);
addRelation("violation", wrapper_rel_violation_0e1a24bba958dc61, false, true);
}

 Sf_souffle6zZFsH::~Sf_souffle6zZFsH(){
}

void Sf_souffle6zZFsH::runFunction(std::string inputDirectoryArg,std::string outputDirectoryArg,bool performIOArg,bool pruneImdtRelsArg){

    this->inputDirectory  = std::move(inputDirectoryArg);
    this->outputDirectory = std::move(outputDirectoryArg);
    this->performIO       = performIOArg;
    this->pruneImdtRels   = pruneImdtRelsArg;

    // set default threads (in embedded mode)
    // if this is not set, and omp is used, the default omp setting of number of cores is used.
#if defined(_OPENMP)
    if (0 < getNumThreads()) { omp_set_num_threads(static_cast<int>(getNumThreads())); }
#endif

    signalHandler->set();
// -- query evaluation --
{
 std::vector<RamDomain> args, ret;
stratum_magic_interm_out_violation_fff__37ba94fccd4ef939.run(args, ret);
}
{
 std::vector<RamDomain> args, ret;
stratum_birthDate_6c79f235432d23a3.run(args, ret);
}
{
 std::vector<RamDomain> args, ret;
stratum_deathDate_257202275e3b218b.run(args, ret);
}
{
 std::vector<RamDomain> args, ret;
stratum_name_7086735a54cc4457.run(args, ret);
}
{
 std::vector<RamDomain> args, ret;
stratum_nationality_4dbdff6917fc0fdb.run(args, ret);
}
{
 std::vector<RamDomain> args, ret;
stratum_occupation_6823ff7471901daa.run(args, ret);
}
{
 std::vector<RamDomain> args, ret;
stratum_person_6a04f477d567ed75.run(args, ret);
}
{
 std::vector<RamDomain> args, ret;
stratum_neglabel_has_name_7c7cb4359766bf2a.run(args, ret);
}
{
 std::vector<RamDomain> args, ret;
stratum_neglabel_has_occupation_222e45352d455374.run(args, ret);
}
{
 std::vector<RamDomain> args, ret;
stratum_interm_out_violation_fff__ba10257fdd44e5f2.run(args, ret);
}
{
 std::vector<RamDomain> args, ret;
stratum_violation_667f1d69f307571b.run(args, ret);
}

// -- relation hint statistics --
signalHandler->reset();
}

void Sf_souffle6zZFsH::run(){
runFunction("", "", false, false);
}

void Sf_souffle6zZFsH::runAll(std::string inputDirectoryArg,std::string outputDirectoryArg,bool performIOArg,bool pruneImdtRelsArg){
runFunction(inputDirectoryArg, outputDirectoryArg, performIOArg, pruneImdtRelsArg);
}

void Sf_souffle6zZFsH::printAll([[maybe_unused]] std::string outputDirectoryArg){
try {std::map<std::string, std::string> directiveMap({{R"_(IO)_",R"_(file)_"},{R"_(attributeNames)_",R"_(entity	constraint	message)_"},{R"_(auxArity)_",R"_(0)_"},{R"_(name)_",R"_(violation)_"},{R"_(operation)_",R"_(output)_"},{R"_(output-dir)_",R"_(results)_"},{R"_(params)_",R"_({"records": {}, "relation": {"arity": 3, "params": ["entity", "constraint", "message"]}})_"},{R"_(types)_",R"_({"ADTs": {}, "records": {}, "relation": {"arity": 3, "types": ["s:symbol", "s:symbol", "s:symbol"]}})_"}});
if (!outputDirectoryArg.empty()) {directiveMap["output-dir"] = outputDirectoryArg;}
IOSystem::getInstance().getWriter(directiveMap, symTable, recordTable)->writeAll(*rel_violation_0e1a24bba958dc61);
} catch (std::exception& e) {std::cerr << e.what();exit(1);}
}

void Sf_souffle6zZFsH::loadAll([[maybe_unused]] std::string inputDirectoryArg){
try {std::map<std::string, std::string> directiveMap({{R"_(IO)_",R"_(file)_"},{R"_(attributeNames)_",R"_(entity	value)_"},{R"_(auxArity)_",R"_(0)_"},{R"_(fact-dir)_",R"_(results/facts)_"},{R"_(name)_",R"_(occupation)_"},{R"_(operation)_",R"_(input)_"},{R"_(params)_",R"_({"records": {}, "relation": {"arity": 2, "params": ["entity", "value"]}})_"},{R"_(types)_",R"_({"ADTs": {}, "records": {}, "relation": {"arity": 2, "types": ["s:symbol", "s:symbol"]}})_"}});
if (!inputDirectoryArg.empty()) {directiveMap["fact-dir"] = inputDirectoryArg;}
IOSystem::getInstance().getReader(directiveMap, symTable, recordTable)->readAll(*rel_occupation_76c3c68cff8238ec);
} catch (std::exception& e) {std::cerr << "Error loading occupation data: " << e.what() << '\n';
exit(1);
}
try {std::map<std::string, std::string> directiveMap({{R"_(IO)_",R"_(file)_"},{R"_(attributeNames)_",R"_(entity)_"},{R"_(auxArity)_",R"_(0)_"},{R"_(fact-dir)_",R"_(results/facts)_"},{R"_(name)_",R"_(person)_"},{R"_(operation)_",R"_(input)_"},{R"_(params)_",R"_({"records": {}, "relation": {"arity": 1, "params": ["entity"]}})_"},{R"_(types)_",R"_({"ADTs": {}, "records": {}, "relation": {"arity": 1, "types": ["s:symbol"]}})_"}});
if (!inputDirectoryArg.empty()) {directiveMap["fact-dir"] = inputDirectoryArg;}
IOSystem::getInstance().getReader(directiveMap, symTable, recordTable)->readAll(*rel_person_4b7efb71e7bbaeee);
} catch (std::exception& e) {std::cerr << "Error loading person data: " << e.what() << '\n';
exit(1);
}
try {std::map<std::string, std::string> directiveMap({{R"_(IO)_",R"_(file)_"},{R"_(attributeNames)_",R"_(entity	value)_"},{R"_(auxArity)_",R"_(0)_"},{R"_(fact-dir)_",R"_(results/facts)_"},{R"_(name)_",R"_(name)_"},{R"_(operation)_",R"_(input)_"},{R"_(params)_",R"_({"records": {}, "relation": {"arity": 2, "params": ["entity", "value"]}})_"},{R"_(types)_",R"_({"ADTs": {}, "records": {}, "relation": {"arity": 2, "types": ["s:symbol", "s:symbol"]}})_"}});
if (!inputDirectoryArg.empty()) {directiveMap["fact-dir"] = inputDirectoryArg;}
IOSystem::getInstance().getReader(directiveMap, symTable, recordTable)->readAll(*rel_name_58440f57e1b2dd1f);
} catch (std::exception& e) {std::cerr << "Error loading name data: " << e.what() << '\n';
exit(1);
}
try {std::map<std::string, std::string> directiveMap({{R"_(IO)_",R"_(file)_"},{R"_(attributeNames)_",R"_(entity	value)_"},{R"_(auxArity)_",R"_(0)_"},{R"_(fact-dir)_",R"_(results/facts)_"},{R"_(name)_",R"_(birthDate)_"},{R"_(operation)_",R"_(input)_"},{R"_(params)_",R"_({"records": {}, "relation": {"arity": 2, "params": ["entity", "value"]}})_"},{R"_(types)_",R"_({"ADTs": {}, "records": {}, "relation": {"arity": 2, "types": ["s:symbol", "s:symbol"]}})_"}});
if (!inputDirectoryArg.empty()) {directiveMap["fact-dir"] = inputDirectoryArg;}
IOSystem::getInstance().getReader(directiveMap, symTable, recordTable)->readAll(*rel_birthDate_9bc1888ef26605d0);
} catch (std::exception& e) {std::cerr << "Error loading birthDate data: " << e.what() << '\n';
exit(1);
}
try {std::map<std::string, std::string> directiveMap({{R"_(IO)_",R"_(file)_"},{R"_(attributeNames)_",R"_(entity	value)_"},{R"_(auxArity)_",R"_(0)_"},{R"_(fact-dir)_",R"_(results/facts)_"},{R"_(name)_",R"_(nationality)_"},{R"_(operation)_",R"_(input)_"},{R"_(params)_",R"_({"records": {}, "relation": {"arity": 2, "params": ["entity", "value"]}})_"},{R"_(types)_",R"_({"ADTs": {}, "records": {}, "relation": {"arity": 2, "types": ["s:symbol", "s:symbol"]}})_"}});
if (!inputDirectoryArg.empty()) {directiveMap["fact-dir"] = inputDirectoryArg;}
IOSystem::getInstance().getReader(directiveMap, symTable, recordTable)->readAll(*rel_nationality_45001e24d435ebbf);
} catch (std::exception& e) {std::cerr << "Error loading nationality data: " << e.what() << '\n';
exit(1);
}
try {std::map<std::string, std::string> directiveMap({{R"_(IO)_",R"_(file)_"},{R"_(attributeNames)_",R"_(entity	value)_"},{R"_(auxArity)_",R"_(0)_"},{R"_(fact-dir)_",R"_(results/facts)_"},{R"_(name)_",R"_(deathDate)_"},{R"_(operation)_",R"_(input)_"},{R"_(params)_",R"_({"records": {}, "relation": {"arity": 2, "params": ["entity", "value"]}})_"},{R"_(types)_",R"_({"ADTs": {}, "records": {}, "relation": {"arity": 2, "types": ["s:symbol", "s:symbol"]}})_"}});
if (!inputDirectoryArg.empty()) {directiveMap["fact-dir"] = inputDirectoryArg;}
IOSystem::getInstance().getReader(directiveMap, symTable, recordTable)->readAll(*rel_deathDate_2a1e0db35f240968);
} catch (std::exception& e) {std::cerr << "Error loading deathDate data: " << e.what() << '\n';
exit(1);
}
}

void Sf_souffle6zZFsH::dumpInputs(){
try {std::map<std::string, std::string> rwOperation;
rwOperation["IO"] = "stdout";
rwOperation["name"] = "occupation";
rwOperation["types"] = R"_({"relation": {"arity": 2, "auxArity": 0, "types": ["s:symbol", "s:symbol"]}})_";
IOSystem::getInstance().getWriter(rwOperation, symTable, recordTable)->writeAll(*rel_occupation_76c3c68cff8238ec);
} catch (std::exception& e) {std::cerr << e.what();exit(1);}
try {std::map<std::string, std::string> rwOperation;
rwOperation["IO"] = "stdout";
rwOperation["name"] = "person";
rwOperation["types"] = R"_({"relation": {"arity": 1, "auxArity": 0, "types": ["s:symbol"]}})_";
IOSystem::getInstance().getWriter(rwOperation, symTable, recordTable)->writeAll(*rel_person_4b7efb71e7bbaeee);
} catch (std::exception& e) {std::cerr << e.what();exit(1);}
try {std::map<std::string, std::string> rwOperation;
rwOperation["IO"] = "stdout";
rwOperation["name"] = "name";
rwOperation["types"] = R"_({"relation": {"arity": 2, "auxArity": 0, "types": ["s:symbol", "s:symbol"]}})_";
IOSystem::getInstance().getWriter(rwOperation, symTable, recordTable)->writeAll(*rel_name_58440f57e1b2dd1f);
} catch (std::exception& e) {std::cerr << e.what();exit(1);}
try {std::map<std::string, std::string> rwOperation;
rwOperation["IO"] = "stdout";
rwOperation["name"] = "birthDate";
rwOperation["types"] = R"_({"relation": {"arity": 2, "auxArity": 0, "types": ["s:symbol", "s:symbol"]}})_";
IOSystem::getInstance().getWriter(rwOperation, symTable, recordTable)->writeAll(*rel_birthDate_9bc1888ef26605d0);
} catch (std::exception& e) {std::cerr << e.what();exit(1);}
try {std::map<std::string, std::string> rwOperation;
rwOperation["IO"] = "stdout";
rwOperation["name"] = "nationality";
rwOperation["types"] = R"_({"relation": {"arity": 2, "auxArity": 0, "types": ["s:symbol", "s:symbol"]}})_";
IOSystem::getInstance().getWriter(rwOperation, symTable, recordTable)->writeAll(*rel_nationality_45001e24d435ebbf);
} catch (std::exception& e) {std::cerr << e.what();exit(1);}
try {std::map<std::string, std::string> rwOperation;
rwOperation["IO"] = "stdout";
rwOperation["name"] = "deathDate";
rwOperation["types"] = R"_({"relation": {"arity": 2, "auxArity": 0, "types": ["s:symbol", "s:symbol"]}})_";
IOSystem::getInstance().getWriter(rwOperation, symTable, recordTable)->writeAll(*rel_deathDate_2a1e0db35f240968);
} catch (std::exception& e) {std::cerr << e.what();exit(1);}
}

void Sf_souffle6zZFsH::dumpOutputs(){
try {std::map<std::string, std::string> rwOperation;
rwOperation["IO"] = "stdout";
rwOperation["name"] = "violation";
rwOperation["types"] = R"_({"relation": {"arity": 3, "auxArity": 0, "types": ["s:symbol", "s:symbol", "s:symbol"]}})_";
IOSystem::getInstance().getWriter(rwOperation, symTable, recordTable)->writeAll(*rel_violation_0e1a24bba958dc61);
} catch (std::exception& e) {std::cerr << e.what();exit(1);}
}

SymbolTable& Sf_souffle6zZFsH::getSymbolTable(){
return symTable;
}

RecordTable& Sf_souffle6zZFsH::getRecordTable(){
return recordTable;
}

void Sf_souffle6zZFsH::setNumThreads(std::size_t numThreadsValue){
SouffleProgram::setNumThreads(numThreadsValue);
symTable.setNumLanes(getNumThreads());
recordTable.setNumLanes(getNumThreads());
regexCache.setNumLanes(getNumThreads());
}

void Sf_souffle6zZFsH::executeSubroutine(std::string name,const std::vector<RamDomain>& args,std::vector<RamDomain>& ret){
if (name == "@interm_out.violation.{fff}") {
stratum_interm_out_violation_fff__ba10257fdd44e5f2.run(args, ret);
return;}
if (name == "@magic.@interm_out.violation.{fff}") {
stratum_magic_interm_out_violation_fff__37ba94fccd4ef939.run(args, ret);
return;}
if (name == "@neglabel.has_name") {
stratum_neglabel_has_name_7c7cb4359766bf2a.run(args, ret);
return;}
if (name == "@neglabel.has_occupation") {
stratum_neglabel_has_occupation_222e45352d455374.run(args, ret);
return;}
if (name == "birthDate") {
stratum_birthDate_6c79f235432d23a3.run(args, ret);
return;}
if (name == "deathDate") {
stratum_deathDate_257202275e3b218b.run(args, ret);
return;}
if (name == "name") {
stratum_name_7086735a54cc4457.run(args, ret);
return;}
if (name == "nationality") {
stratum_nationality_4dbdff6917fc0fdb.run(args, ret);
return;}
if (name == "occupation") {
stratum_occupation_6823ff7471901daa.run(args, ret);
return;}
if (name == "person") {
stratum_person_6a04f477d567ed75.run(args, ret);
return;}
if (name == "violation") {
stratum_violation_667f1d69f307571b.run(args, ret);
return;}
fatal(("unknown subroutine " + name).c_str());
}

} // namespace  souffle
namespace souffle {
SouffleProgram *newInstance_souffle6zZFsH(){return new  souffle::Sf_souffle6zZFsH;}
SymbolTable *getST_souffle6zZFsH(SouffleProgram *p){return &reinterpret_cast<souffle::Sf_souffle6zZFsH*>(p)->getSymbolTable();}
} // namespace souffle

#ifndef __EMBEDDED_SOUFFLE__
#include "souffle/CompiledOptions.h"
int main(int argc, char** argv)
{
try{
souffle::CmdOptions opt(R"_(results/validation.dl)_",
R"_()_",
R"_()_",
false,
R"_()_",
4);
if (!opt.parse(argc,argv)) return 1;
souffle::Sf_souffle6zZFsH obj;
#if defined(_OPENMP) 
obj.setNumThreads(opt.getNumJobs());

#endif
obj.runAll(opt.getInputFileDir(), opt.getOutputFileDir());
return 0;
} catch(std::exception &e) { souffle::SignalHandler::instance()->error(e.what());}
}
#endif

namespace  souffle {
using namespace souffle;
class factory_Sf_souffle6zZFsH: souffle::ProgramFactory {
public:
souffle::SouffleProgram* newInstance();
 factory_Sf_souffle6zZFsH();
private:
};
} // namespace  souffle
namespace  souffle {
using namespace souffle;
souffle::SouffleProgram* factory_Sf_souffle6zZFsH::newInstance(){
return new  souffle::Sf_souffle6zZFsH();
}

 factory_Sf_souffle6zZFsH::factory_Sf_souffle6zZFsH():
souffle::ProgramFactory("souffle6zZFsH"){
}

} // namespace  souffle
namespace souffle {

#ifdef __EMBEDDED_SOUFFLE__
extern "C" {
souffle::factory_Sf_souffle6zZFsH __factory_Sf_souffle6zZFsH_instance;
}
#endif
} // namespace souffle

