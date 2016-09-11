"""
Preprocessing of the Monroe Plan Corpus for copct:
- Converts from lisp data to Python tuples
- Extracts intermediate states for every plan in the corpus
- Reformats intentions into (state, task, parameters) form
"""
from monroe_static import locs, watercos, powercos, poslocs, sleaders, gens, food, pcrews
from monroe_utils import unify, single_unify

def parse_monroe(infilename='monroe5000.txt', outfilename='monroe5000.py'):
    """
    Rewrite the Monroe corpus lisp data file as a tuple in a python script.
    All symbols are converted to strings.
    Inputs:
        infilename: filename from which the lisp data is read
        outfilename: filename to which the python script is written
    """
    infile = open(infilename,"r")
    outfile = open(outfilename,"w")
    outfile.write("corpus = (\n")
    syntax_chars = "() \t\n" # lisp syntax
    previous_char = " "
    for line in infile:
        for char in line:
            if (previous_char in syntax_chars) != (char in syntax_chars):
                # just changed between syntax and symbol, quote symbol for python
                outfile.write("\"")
                # separate symbols with commas for python
                if char in syntax_chars: outfile.write(",")
            # separate sub-lists with commas for python
            if previous_char == ")": outfile.write(",")
            # write current character and advance
            outfile.write(char)
            previous_char = char
    outfile.write(")")
    infile.close()
    outfile.close()

def populate_states_from_op(pre_states, op):
    """
    Infers additional facts that must have been true in the previous states for the op to be applied successfully.
    Returns the states with the additional facts added.
    This implementation has a separate case for every operator in the Monroe domain.
    Inputs:
        op: a grounded operator of the form (name, arg1, arg2, ...)
        pre_states: the states leading up to the application of the operator.
            pre_states[i] is the i^{th} state, of the form (objs, facts).
            objs is a list of possible parameter values, facts is a list of relations over those objects.
    Outputs:
        states[i]: the states with additional facts added.
        if op is a primitive action, the last element is a new state after op was applied.
    """
    objs = pre_states[-1][0]
    # facts true before and after operator is applied (may be altered)
    pre_facts = set(pre_states[-1][1])
    task = op[0]
    """
    (:operator (!navegate-vehicle ?person ?veh ?loc)
	     ((person ?person) (vehicle ?veh) (atloc ?veh ?vehloc)
	      (atloc ?person ?vehloc) (can-drive ?person ?veh)
	      (not (wrecked-car ?veh)))
	     ((atloc ?veh ?vehloc) (atloc ?person ?vehloc))
	     ((atloc ?veh ?loc) (atloc ?person ?loc)))
    """
    if task == '!NAVEGATE-VEHICLE':
        person, veh, loc = op[1:]
        for s in range(len(pre_states)):
            pre_states[s] = (objs, tuple(set(pre_states[s][1]) | set((('PERSON', person), ('VEHICLE', veh)))))
        post_facts = pre_facts | set((('ATLOC', veh, loc), ('ATLOC', person, loc)))
        vehloc, = single_unify(pre_facts, ('ATLOC', veh, None), ('ATLOC', person, None))
        if vehloc is not None:
            pre_facts |= set((('ATLOC', veh, vehloc), ('ATLOC', person, vehloc)))
            post_facts -= set((('ATLOC', veh, vehloc), ('ATLOC', person, vehloc)))
        pre_states[-1] = (objs, tuple(pre_facts))
        post_state = (objs, tuple(post_facts))
        return pre_states + [post_state]
    """
    (:operator (!climb-in ?obj ?veh) 
	     ((atloc ?obj ?objloc) (atloc ?veh ?objloc) (fit-in ?obj ?veh))
	     ((atloc ?obj ?objloc))
	     ((atloc ?obj ?veh)))
    """
    if task == '!CLIMB-IN':
        obj, veh = op[1:]
        post_facts = pre_facts | set((('ATLOC', obj, veh),))
        objloc, = single_unify(pre_facts, ('ATLOC', obj, None), ('ATLOC', veh, None))
        if objloc is not None:
            pre_facts.add(('ATLOC', obj, objloc))
            post_facts.discard(('ATLOC', obj, objloc))
        pre_states[-1] = (objs, tuple(pre_facts))
        post_state = (objs, tuple(post_facts))
        return pre_states + [post_state]
    """
    (:operator (!climb-out ?obj ?veh) 
	     ((atloc ?obj ?veh) (atloc ?veh ?vehloc)) 
	     ((atloc ?obj ?veh)) 
	     ((atloc ?obj ?vehloc)))
    """
    if task == '!CLIMB-OUT':
        obj, veh = op[1:]
        pre_facts.add(('ATLOC', obj, veh))
        post_facts = pre_facts - set((('ATLOC', obj, veh),))
        vehloc, = single_unify(pre_facts, ('ATLOC', veh, None))
        if vehloc is not None:
            post_facts.add(('ATLOC', obj, vehloc))
        pre_states[-1] = (objs, tuple(pre_facts))
        post_state = (objs, tuple(post_facts))
        return pre_states + [post_state]
    """
    (:operator (!load ?person ?obj ?veh) 
	     ((atloc ?obj ?objloc) 
	      (atloc ?veh ?objloc) 
	      (atloc ?person ?objloc)
	      (fit-in ?obj ?veh))
	     ((atloc ?obj ?objloc))
	     ((atloc ?obj ?veh)))
    """
    if task == '!LOAD':
        person, obj, veh = op[1:]
        for s in range(len(pre_states)):
            pre_states[s] = (objs, tuple(set(pre_states[s][1]) | set((('FIT-IN', obj, veh),))))
        post_facts = set(pre_facts) | set((('ATLOC', obj, veh),))
        objloc, = single_unify(pre_facts, *[('ATLOC', param, None) for param in op[1:]])
        if objloc is not None:
            pre_facts |= set(tuple(('ATLOC', param, objloc) for param in op[1:]))
            post_facts.discard(('ATLOC', obj, objloc))
        pre_states[-1] = (objs, tuple(pre_facts))
        post_state = (objs, tuple(post_facts))
        return pre_states + [post_state]
    """
    (:operator (!unload ?person ?obj ?veh) 
	     ((atloc ?obj ?veh) (atloc ?veh ?vehloc) (atloc ?person ?vehloc)) 
	     ((atloc ?obj ?veh))
	     ((atloc ?obj ?vehloc)))
    """
    if task == '!UNLOAD':
        person, obj, veh = op[1:]
        pre_facts |= set((('ATLOC', obj, veh),))
        post_facts = set(pre_facts) - set((('ATLOC', obj, veh),))
        vehloc, = single_unify(pre_facts, *[('ATLOC', param, None) for param in [veh, person]])
        if vehloc is not None:
            pre_facts |= set(tuple(('ATLOC', param, vehloc) for param in [veh, person]))
            post_facts.add(('ATLOC', obj, vehloc))
        pre_states[-1] = (objs, tuple(pre_facts))
        post_state = (objs, tuple(post_facts))
        return pre_states + [post_state]
    """
    (:operator (!treat ?emt ?person) 
	     ((atloc ?person ?ploc) (atloc ?emt ?ploc))
	     ()
	     ())
    """
    if task == '!TREAT':
        emt, person = op[1:]
        ploc, = single_unify(pre_facts, *[('ATLOC', param, None) for param in [emt, person]])
        if ploc is not None:
            pre_facts |= set(tuple(('ATLOC', param, ploc) for param in [emt, person]))
        post_facts = set(pre_facts)
        pre_states[-1] = (objs, tuple(pre_facts))
        post_state = (objs, tuple(post_facts))
        return pre_states + [post_state]
    """
    (:operator (!treat-in-hospital ?person ?hospital) 
	     ((atloc ?person ?hospital))
	     ()
	     ())
    """
    if task == 'TREAT-IN-HOSPITAL':
        pre_facts |= set((('ATLOC', op[1], op[2]),))
        post_facts = set(pre_facts)
        pre_states[-1] = (objs, tuple(pre_facts))
        post_state = (objs, tuple(post_facts))
        return pre_states + [post_state]
    """
    ;;set-up-shelter sets up a shelter at a certain location
    (:method (set-up-shelter ?loc)
	   normal
	   ((shelter-leader ?leader)
	    (not (assigned-to-shelter ?leader ?other-shelter))
	    (food ?food))
	   ((get-electricity ?loc) (get-to ?leader ?loc) (get-to ?food ?loc)))
    """
    if task == 'SET-UP-SHELTER': return pre_states # could do better with tree?
    """
    ;;fix-water-main
    (:method (fix-water-main ?from ?to)
	   normal
	   ()
	   ((shut-off-water ?from ?to) 
	    (repair-pipe ?from ?to)
	    (turn-on-water ?from ?to)))
    """
    if task == 'FIX-WATER-MAIN': return pre_states # no information
    """
    ;; clear-road-hazard - cleans up a hazardous spill
    (:method (clear-road-hazard ?from ?to)
	   normal
	   ()
	   ((block-road ?from ?to)
	    (clean-up-hazard ?from ?to)
	    (unblock-road ?from ?to)))
    """
    if task == 'CLEAR-ROAD-HAZARD': return pre_states # no information
    """
    ;; clear-road-wreck - gets a wreck out of the road
    (:method (clear-road-wreck ?from ?to)
	   normal
	   ()
	   ((set-up-cones ?from ?to)
	    (clear-wreck ?from ?to)
	    (take-down-cones ?from ?to)))
    """
    if task == 'CLEAR-ROAD-WRECK': return pre_states # no information
    """
    ;; clear-road-tree
    (:method (clear-road-tree ?from ?to) ;; clears a tree that's in the road
	   normal
	   ((tree-blocking-road ?from ?to ?tree))
	   ((set-up-cones ?from ?to)
	    (clear-tree ?tree)
	    (take-down-cones ?from ?to)))
    """
    if task == 'CLEAR-ROAD-TREE': return pre_states # no information not already in subs
    """
    ;; plow-road
    (:method (plow-road ?from ?to)
	   plow
	   ((road-snowy ?from ?to)
	    (snowplow ?plow)
	    (atloc ?plow ?plowloc)
	    (plowdriver ?driver)
	    )
	   ((get-to ?driver ?plowloc)
	    (!navegate-snowplow ?driver ?plow ?from) ;; must use nav-snowplow
	                        ;; since regular cars can't drive if snowy
	    (!engage-plow ?driver ?plow)
	    (!navegate-snowplow ?driver ?plow ?to)
	    (!disengage-plow ?driver ?plow)))
    """
    if task == 'PLOW-ROAD': return pre_states # road-snowy worth it?
    """
    ;;quell-riot
    (:method (quell-riot ?loc)
	   with-police
	   ((in-town ?loc ?town)
	    (police-unit ?p1) (police-unit ?p2) (not (equal ?p1 ?p2)))
	   ((declare-curfew ?town) (get-to ?p1 ?loc) (get-to ?p2 ?loc)
	    (!set-up-barricades ?p1) (!set-up-barricades ?p2)))
    """
    if task == 'QUELL-RIOT': return pre_states #
    """
    ;;provide-temp-heat
    (:method (provide-temp-heat ?person)
	   to-shelter
	   ((person ?person) (shelter ?shelter))
	   ((get-to ?person ?shelter)))
    (:method (provide-temp-heat ?person)
	   local-electricity
	   ((person ?person) (atloc ?person ?ploc))
	   ((generate-temp-electricity ?ploc) (!turn-on-heat ?ploc)))
    """
    if task == 'PROVIDE-TEMP-HEAT': return pre_states #
    """
    ;;fix-power-line
    (:method (fix-power-line ?lineloc)
	   normal
	   ((power-crew ?crew) (power-van ?van))
	   ((get-to ?crew ?lineloc) (get-to ?van ?lineloc)
	    (repair-line ?crew ?lineloc)))
    """
    if task == 'FIX-POWER-LINE': return pre_states #
    """
    ;;provide-medical-attention
    (:method (provide-medical-attention ?person)
	   in-hospital
	   ((hospital ?hosp) (has-condition ?person ?cond)
	    (not (hospital-doesnt-treat ?hosp ?cond)))
	   ((get-to ?person ?hosp) (!treat-in-hospital ?person ?hosp)))
    (:method (provide-medical-attention ?person)
	   simple-on-site
	   ((has-condition ?person ?cond) (not (serious-condition ?cond)))
	   ((emt-treat ?person)))
    """
    if task == 'PROVIDE-MEDICAL-ATTENTION': return pre_states
    """
    ;;;;;;;;;;;;;;;;;;; subgoals ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    ;; clean-up-hazard
    (:method (clean-up-hazard ?from ?to)
	   very-hazardous ;; just call the feds
	   ((hazard-seriousness ?from ?to very-hazardous))
	   ((!call fema))
	   normal ;; we can take care of it
	   ((hazard-team ?ht))
	   ((get-to ?ht ?from) (!clean-hazard ?ht ?from ?to)))
    """
    if task == 'CLEAN-UP-HAZARD':
        # kludge: should only add if child is call fema (needs tree not just op)
        fromloc, toloc = op[1:]
        pre_states[-1] = (objs, tuple(set(pre_states[-1][1]) | set((('HAZARD-SERIOUSNESS', fromloc, toloc, 'VERY-HAZARDOUS'),))))
        return pre_states
    """
    ;; block-road - blocks off a road
    (:method (block-road ?from ?to)
	   normal
	   ((police-unit ?police))
	   (:unordered (set-up-cones ?from ?to)
	    (get-to ?police ?from)))
    """
    if task == 'BLOCK-ROAD': return pre_states #
    """
    ;; unblock-road - unblocks a road
    (:method (unblock-road ?from ?to)
	   normal
	   ()
	   ((take-down-cones ?from ?to)))
    """
    if task == 'UNBLOCK-ROAD': return pre_states #
    """
    ;; get-electricity provides electricity to a site (if not already there)
    (:method (get-electricity ?loc)
	   already-has-electricity ;; do nothing
	   ((not (no-electricity ?loc)))
	   ()
           no-electricity
	   ()
	   ((generate-temp-electricity ?loc))
	   )
    """
    if task == 'GET-ELECTRICITY': return pre_states #
    """
    ;; repair-pipe
    (:method (repair-pipe ?from ?to) ;; repairs a pipe at location
	   normal
	   ((water-crew ?crew))
	   ((get-to ?crew ?from)
	    (set-up-cones ?from ?to)
	    (open-hole ?from ?to)
	    (!replace-pipe ?crew ?from ?to)
	    (close-hole ?from ?to)
	    (take-down-cones ?from ?to)))
    """
    if task == 'REPAIR-PIPE': return pre_states
    """
    ;; open-hole
    (:method (open-hole ?from ?to) ;; opens a hole in the street
	   normal
	   ((backhoe ?backhoe))
	   ((get-to ?backhoe ?from)
	    (!dig ?backhoe ?from)))
    """
    if task == 'OPEN-HOLE': return pre_states # want toloc but no way to get it
    """
    ;; close-hole
    (:method (close-hole ?from ?to) ;; opens a hole in the street
	   normal
	   ((backhoe ?backhoe))
	   ((get-to ?backhoe ?from)
	    (!fill-in ?backhoe ?from)))
    """
    if task == 'CLOSE-HOLE': return pre_states # want toloc but no way to get it
    """
    ;; set-up-cones
    (:method (set-up-cones ?from ?to) ;; sets up orange cones at road
	   normal
	   ((work-crew ?crew))
	   ((get-to ?crew ?from) (!place-cones ?crew)))
    """
    if task == 'SET-UP-CONES': return pre_states # want toloc but no way to get it
    """
    ;; take-down-cones
    (:method (take-down-cones ?from ?to) ;; takes down cones
	   normal
	   ((work-crew ?crew))
	   ((get-to ?crew ?from) (!pickup-cones ?crew)))
    """
    if task == 'TAKE-DOWN-CONES': return pre_states # want toloc but no way to get it
    """
    ;; clear-wreck
    (:method (clear-wreck ?from ?to) ;; gets rid of a wreck in any loc
	   normal
	   ((wrecked-vehicle ?from ?to ?veh) (garbage-dump ?dump))
	   ((tow-to ?veh ?dump)))
    """
    if task == 'CLEAR-WRECK':
        # kludge - can't get ?veh, use None as placeholder (it's never used by causes function)
        fromloc, toloc = op[1:]
        pre_states[-1] = (objs, tuple(pre_facts | set((('WRECKED-VEHICLE', fromloc, toloc, None),))))
        return pre_states
    """
    ;; tow-to - tows a vehicle somewhere
    (:method (tow-to ?veh ?to)
	   normal
	   ((tow-truck ?ttruck) (vehicle ?veh) (atloc ?veh ?vehloc))
	   ((get-to ?ttruck ?vehloc)
	    (!hook-to-tow-truck ?ttruck ?veh)
	    (get-to ?ttruck ?to)
	    (!unhook-from-tow-truck ?ttruck ?veh)))
    """
    if task == 'TOW-TO': return pre_states #
    """
    ;; clear-tree
    (:method (clear-tree ?tree) ;; this gets rid of a tree in any loc
	   normal
	   ((tree-crew ?tcrew) (tree ?tree) 
	    (atloc ?tree ?treeloc))
	   ((get-to ?tcrew ?treeloc) (!cut-tree ?tcrew ?tree)
	    (remove-blockage ?tree)))
    """
    if task == 'CLEAR-TREE': return pre_states #
    """
    ;; remove-blockage
    (:method (remove-blockage ?stuff)
	   move-to-side-of-street
	   ((work-crew ?crew) (atloc ?stuff ?loc))
	   ((get-to ?crew ?loc)
	    (!carry-blockage-out-of-way ?crew ?stuff)))
    (:method (remove-blockage ?stuff)
	   carry-away
	   ((garbage-dump ?dump))
	   ((get-to ?stuff ?dump)))
    """
    if task == 'REMOVE-BLOCKAGE': return pre_states #
    """
    ;; declare-curfew
    (:method (declare-curfew ?town)
	   normal
	   ()
	   (:unordered (!call EBS) (!call police-chief)))
    """
    if task == 'REMOVE-BLOCKAGE': return pre_states
    """
    ;; generate-temp-electricity
    (:method (generate-temp-electricity ?loc)
	   with-generator
	   ((generator ?gen))
	   ((make-full-fuel ?gen) (get-to ?gen ?loc) (!hook-up ?gen ?loc)
	    (!turn-on ?gen)))
    """
    if task == 'GENERATE-TEMP-ELECTRICITY': return pre_states #
    """
    ;; make-full-fuel - makes sure arg1 is full of fuel
    (:method (make-full-fuel ?gen)
	   with-gas-can
	   ((gas-can ?gc) (atloc ?gen ?genloc) (service-station ?ss))
	   ((get-to ?gc ?ss) (add-fuel ?ss ?gc) (get-to ?gc ?genloc)
	    (!pour-into ?gc ?gen)))
    (:method (make-full-fuel ?gen)
	   at-service-station
	   ((service-station ?ss))
	   ((get-to ?gen ?ss) (add-fuel ?ss ?gen)))
    """
    if task == 'MAKE-FULL-FUEL': return pre_states #
    """
    ;; add-fuel (at service-station)
    (:method (add-fuel ?ss ?obj)
	   normal
	   ()
	   (:unordered (!pay ?ss) (!pump-gas-into ?ss ?obj)))
    """
    if task == 'ADD-FUEL': return pre_states
    """
    ;; repair-line
    (:method (repair-line ?crew ?lineloc)
	   with-tree
	   ((tree ?tree) (atloc ?tree ?lineloc)
	    (atloc ?crew ?lineloc))
	   ((shut-off-power ?crew ?lineloc) 
	    (:unordered (clear-tree ?tree) 
			(!remove-wire ?crew ?lineloc))
	    (!string-wire ?crew ?lineloc) (turn-on-power ?crew ?lineloc))
	   without-tree
	   ((atloc ?crew ?lineloc))
	   ((shut-off-power ?crew ?lineloc) 
	    (!remove-wire ?crew ?lineloc)
	    (!string-wire ?crew ?lineloc) (turn-on-power ?crew ?lineloc)))
    """
    if task == 'REPAIR-LINE': return pre_states #
    """
    ;; shut-off-power
    (:method (shut-off-power ?crew ?loc)
	   normal
	   ((in-town ?loc ?town) (powerco-of ?town ?powerco))
	   (!call ?powerco))
    """
    if task == 'SHUT-OFF-POWER': return pre_states # narrow loc to town through fixed state in causes
    """
    ;; turn-on-power
    (:method (turn-on-power ?crew ?loc)
	   normal
	   ((in-town ?loc ?town) (powerco-of ?town ?powerco))
	   (!call ?powerco))
    """
    if task == 'TURN-ON-POWER': return pre_states # narrow loc to town through fixed state in causes
    """
    ;; shut-off-water
    (:method (shut-off-water ?from ?to)
	   normal
	   ((in-town ?from ?town) (waterco-of ?town ?waterco))
	   ((!call ?waterco)))
    """
    if task == 'SHUT-OFF-WATER': return pre_states # narrow loc to town through fixed state in causes
    """
    ;; turn-on-water
    (:method (turn-on-water ?from ?to)
	   normal
	   ((in-town ?from ?town) (waterco-of ?town ?waterco))
	   ((!call ?waterco)))
    """
    if task == 'TURN-ON-WATER': return pre_states # narrow loc to town through fixed state in causes
    """
    ;; emt-treat
    (:method (emt-treat ?person)
	   emt
	   ((emt-crew ?emt) (atloc ?person ?personloc))
	   ((get-to ?emt ?personloc) (!treat ?emt ?person)))
    """
    if task == 'EMT-TREAT': return pre_states
    """
    ;; stabilize
    (:method (stabilize ?person)
	   emt
	   ()
	   ((emt-treat ?person)))
    """
    if task == 'STABILIZE': return pre_states
    """
    ;; get-to
    (:method (get-to ?obj ?place)
	   already-there
	   ((atloc ?obj ?place))
	   ())
    (:method (get-to ?person ?place)
	   person-drives-themself
	   ((not (atloc ?person ?place))
	    (person ?person) (vehicle ?veh) (atloc ?veh ?vehloc)
	    (atloc ?person ?vehloc))
	   ((drive-to ?person ?veh ?place)))
    (:method (get-to ?veh ?place)
	   vehicle-gets-driven
	   ((not (atloc ?veh ?place))
	    (person ?person)
	    (vehicle ?veh) (atloc ?veh ?vehloc)
	    (atloc ?person ?vehloc)
	    )
	   ((drive-to ?person ?veh ?place)))
    (:method (get-to ?obj ?place)
	   as-cargo
	   ((not (atloc ?obj ?place))
	   (vehicle ?veh)
	   (atloc ?obj ?objloc)  (fit-in ?obj ?veh)
	   (not (non-ambulatory ?obj)))
	   ((get-to ?veh ?objloc) (get-in ?obj ?veh) (get-to ?veh ?place)
	    (get-out ?obj ?veh))
	   with-ambulance ;; same as above, just with ambulance
	   ((not (atloc ?obj ?place))
	    (atloc ?obj ?objloc) (ambulance ?veh) (fit-in ?obj ?veh)
	    )
	   ((get-to ?veh ?objloc) (stabilize ?obj) (get-in ?obj ?veh)
	    (get-to ?veh ?place) (get-out ?obj ?veh))
	   )
    """
    if task == 'GET-TO': return pre_states # all info in subs except for nop case
    """
    (:method (drive-to ?person ?veh ?loc)
	   normal
	   ((person ?person) (vehicle ?veh) (atloc ?veh ?vehloc)
	    (atloc ?person ?vehloc) (can-drive ?person ?veh))
	   ((!navegate-vehicle ?person ?veh ?loc)))
    """
    if task == 'DRIVE-TO': return pre_states # all info in subs
    """
    (:method (get-in ?obj ?veh)
	   ambulatory-person
	   ((atloc ?obj ?objloc) (atloc ?veh ?objloc) 
	    (person ?obj) (not (non-ambulatory ?obj)))
	   (!climb-in ?obj ?veh)
	   load-in
	   ((atloc ?obj ?objloc) (atloc ?veh ?objloc)
	    (person ?person) (can-lift ?person ?obj))
	   ((get-to ?person ?objloc) (!load ?person ?obj ?veh)))
    """
    if task == 'GET-IN': return pre_states # all info in subs
    """
    (:method (get-out ?obj ?veh)
	   ambulatory-person
	   ((person ?obj) (not (non-ambulatory ?obj)))
	   (!climb-out ?obj ?veh)
	   unload
	   ((atloc ?veh ?vehloc) (person ?person) (can-lift ?person ?obj))
	   ((get-to ?person ?vehloc) (!unload ?person ?obj ?veh)))
    """
    if task == 'GET-OUT': return pre_states # all info in subs
    # remaining operators (all primitive, empty preconds/adds/deletes)
    return pre_states + pre_states[-1:]

def extract_leaves(tree):
    """
    Extract the leaves of a plan decomposition tree in the Monroe corpus.
    Inputs:
       tree: the plan tree, of the form (node, subtree1, subtree2, ...)
            node is a grounded operator of the form (name, arg1, arg2, ...)
    Outputs:
        leaves[i]: The i^{th} leaf, also a grounded operator of the form (name, arg1, arg2, ...) 
    """
    if type(tree[0])==str: # base case, "tree" is a node
        return (tree,)
    else: # recursive case, tree is a tree, recurse on subtrees
        return reduce(lambda x,y: x+y, map(extract_leaves, tree[1:]))

def extract_objects(tree):
    """
    Extract all "objects," the arguments occurring in any operator in a plan decomposition tree.
    This omits static objects always present in every plan of the corpus (locations, etc)
    Inputs:
        tree: the plan tree, as in extract_leaves
    Outputs:
        objs: the set of all distinct objects occurring in the tree
    """
    objs = set()
    if type(tree[0])==str: # base case, "tree" is a node
        objs |= set(tree[1:])
    else: # recursive case
        objs |= set(tree[0][1:])
        for sub in tree[1:]:
            objs |= extract_objects(sub)
    objs -= set(locs) | set(watercos) | set(powercos) # remove static objects
    return objs

def extract_children(tree):
    """
    Extract the immediate child nodes of a tree root
    Inputs:
        tree: a plan decomposition tree
    Outputs:
        children: the immediate child nodes of root (with their own subtrees omitted)
    """
    return tuple(child if type(child[0])==str else child[0] for child in tree[1:])

# def search_tree(tree):
#     # used to rule out empty-case of get-to
#     if type(tree[0]) != str:
#         if tree[0][0]=='GET-TO' and len(tree)==1: return True
#         return any([search_tree(sub) for sub in tree[1:]])
#     return False

def populate_tree_states(leading_states, next_tree):
    """
    Uses populate_states_from_op on every operator in a plan tree.
    Implementation is recursive; should be called at the top level with:
        leading_states = [(objs, ())]
        next_tree = the full plan tree
    Inputs:
        leading_states: a list of states leading up to next_tree
        next_tree: the next plan tree of operators being applied
    Outputs:
        states: leading states with new facts added, and new states resulting from the next_tree
    """
    if type(next_tree[0])==str: # base case, "tree" is primitive operator
        states = populate_states_from_op(leading_states, next_tree) # = pre_states + [post_state]
    else: # recursive case, process each op in next_tree, starting with root
        states = populate_states_from_op(leading_states, next_tree[0]) # = pre_states
        for sub in next_tree[1:]:
            states = populate_tree_states(states, sub) # = pre_states + post_states
    return states

def preprocess_plan(plan_tree):
    """
    Preprocess a single plan tree from the corpus, populating intermediate states.
    The returned sequences contain elements of the form (state, task_name, (arg1, arg2, ...))
    Inputs:
        plan_tree: a plan tree from the monroe corpus, in python tuple format (as written by parse_monroe).
    Outputs:
        u: the top-level ground-truth (singleton) sequence
        v: the immediate child sequence of u (ground-truth for modified Monroe experiments)
        w: the bottom-level observed actions
    """
    # pull out data
    root = plan_tree[0]
    children = extract_children(plan_tree)
    objs = extract_objects(plan_tree)
    actions = extract_leaves(plan_tree)
    states = populate_tree_states([(tuple(objs), ())], plan_tree)
    # recover the action indices covered by each child, so that the correct intermediate states are associated
    indices = [0]
    for subtree in plan_tree[1:]:
        indices.append(indices[-1] + len(extract_leaves(subtree)))
    # convert to (state, task, args) format
    u = ((states[0], root[0], root[1:]),)
    v = tuple((states[indices[k]], children[k][0], children[k][1:]) for k in range(len(children)))
    w = tuple((states[i], actions[i][0], actions[i][1:]) for i in range(len(actions)))
    return u, v, w

if __name__ == "__main__":
    # Parse Monroe lisp to python
    print('Parsing lisp...')
    parse_monroe()

    # preprocess each plan tree
    print('Preprocessing plan trees...')
    from monroe5000 import corpus
    corpus = tuple(preprocess_plan(plan_tree) for plan_tree in corpus)

    # Write preprocessed corpus to file
    print('Writing to file...')
    corpus_file = open('monroe_corpus.py','w')
    corpus_file.write('corpus = [')
    for example in corpus:
        corpus_file.write('%s,\n'%str(example))
    corpus_file.write(']\n')
    corpus_file.close()
