"""
The Monroe domain knowledge base, re-encoded as a copct causal relation.
The causes function is implemented with two separate sub-routines:
One for the top-level causes, and one for all other mid-level causes.
This way the top-level causes can be easily omitted in the modified Monroe experiments.

The causes functions have a separate case for each rule in the original knowledge base.
Original lisp rule for each case is copied verbatim in the comments.
Original lisp operator format is:
(:method (name param1 param2 ...) branch1 branch2 ...)
Branch format is:
  branch-label
  (precond1 precond2 ...)
  (subtask1 subtask2 ...)

Sometimes effects are omitted from the original corpus data if they wouldn't change anything.
For example, a GET-TO will be missing if things are already where they need to be gotten to.
Additional cases are included in the causes implementation for these situations.

"""
from monroe_static import locs, watercos, powercos, poslocs, sleaders, gens, food, pcrews
from monroe_utils import unify, single_unify

"""
M: maximum length of v for all (u,v) in causal relation
"""
M = 6

def mid_causes(v):
    """
    Encodes all mid-level causal relations in the knowledge base.
    Inputs:
        v: A sequence of tasks in the form (state, taskname, parameters)
            Each state has the form (objects, facts)
    Outputs:
        g: The set of all possible causes of v, each also in the form (state, taskname, parameters).
    """
    states = tuple(s for (s,t,x) in v) # states (each of the form (objs, facts))
    tasknames = tuple(t for (s,t,x) in v) # Task names
    params = tuple((None,)+x for (s,t,x) in v) # Parameter lists, leading None for task name offset
    g = set()
    """
    ;; clean-up-hazard
    (:method (clean-up-hazard ?from ?to)
	   very-hazardous ;; just call the feds
	   ((hazard-seriousness ?from ?to very-hazardous))
	   ((!call fema))

	   normal ;; we can take care of it
	   ((hazard-team ?ht))
	   ((get-to ?ht ?from) (!clean-hazard ?ht ?from ?to)))
    """
    if tasknames == ('!CALL',) and params[0][1] == 'FEMA':
        m = unify(states[0][1], ('HAZARD-SERIOUSNESS', None, None, 'VERY-HAZARDOUS'))
        for (fromloc, toloc) in m:
            g.add((states[0],'CLEAN-UP-HAZARD', (fromloc, toloc)))
    if tasknames == ('GET-TO','!CLEAN-HAZARD'):
        fromloc, toloc = params[1][2], params[1][3]
        if fromloc == params[0][2]:
            g.add((states[0],'CLEAN-UP-HAZARD', (fromloc, toloc)))
    # Missing get-to
    if tasknames == ('!CLEAN-HAZARD',):
        fromloc, toloc = params[0][2], params[0][3]
        g.add((states[0],'CLEAN-UP-HAZARD', (fromloc, toloc)))
    """
    ;; block-road - blocks off a road
    (:method (block-road ?from ?to)
	   normal
	   ((police-unit ?police))
    (:unordered (set-up-cones ?from ?to)
	    (get-to ?police ?from)))
    """
    if tasknames == ('SET-UP-CONES','GET-TO'):
        fromloc, toloc = params[0][1], params[0][2]
        if fromloc == params[1][2]:
            g.add((states[0],'BLOCK-ROAD', (fromloc, toloc)))
    if tasknames == ('GET-TO','SET-UP-CONES'):
        fromloc, toloc = params[1][1], params[1][2]
        if fromloc == params[0][2]:
            g.add((states[0],'BLOCK-ROAD', (fromloc, toloc)))
    # Missing get-to
    if tasknames == ('SET-UP-CONES',):
        fromloc, toloc = params[0][1], params[0][2]
        g.add((states[0],'BLOCK-ROAD', (fromloc, toloc)))
    """
    ;; unblock-road - unblocks a road
    (:method (unblock-road ?from ?to)
	   normal
	   ()
	   ((take-down-cones ?from ?to)))
    """
    if tasknames == ('TAKE-DOWN-CONES',):
        fromloc, toloc = params[0][1], params[0][2]
        g.add((states[0],'UNBLOCK-ROAD', (fromloc, toloc)))
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
    if tasknames == ('GENERATE-TEMP-ELECTRICITY',):
        loc = params[0][1]
        g.add((states[0],'GET-ELECTRICITY', (loc,)))
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
    if tasknames == ('GET-TO','SET-UP-CONES','OPEN-HOLE','!REPLACE-PIPE','CLOSE-HOLE','TAKE-DOWN-CONES'):
        fromloc, toloc = params[0][2], params[1][2]
        if (fromloc == params[1][1] == params[2][1] == params[3][2] == params[4][1] == params[5][1]) and (toloc == params[2][2] == params[3][3] == params[4][2] == params[5][2]): 
            g.add((states[0],'REPAIR-PIPE', (fromloc, toloc)))
    # Missing get-to
    if tasknames == ('SET-UP-CONES','OPEN-HOLE','!REPLACE-PIPE','CLOSE-HOLE','TAKE-DOWN-CONES'):
        fromloc, toloc = params[0][1], params[0][2]
        if (fromloc == params[1][1] == params[2][2] == params[3][1] == params[4][1]) and (toloc == params[2][3] == params[3][2] == params[4][2]): 
            g.add((states[0],'REPAIR-PIPE', (fromloc, toloc)))
    """
    ;; open-hole
    (:method (open-hole ?from ?to) ;; opens a hole in the street
	   normal
	   ((backhoe ?backhoe))
	   ((get-to ?backhoe ?from)
	    (!dig ?backhoe ?from)))
    """
    if tasknames == ('GET-TO','!DIG'):
        fromloc = params[0][2]
        if fromloc == params[1][2]:
            for toloc in poslocs:
                g.add((states[0],'OPEN-HOLE', (fromloc, toloc)))
    # Missing get-to
    if tasknames == ('!DIG',):
        fromloc = params[0][2]
        for toloc in poslocs:
            g.add((states[0],'OPEN-HOLE', (fromloc, toloc)))
    """
    ;; close-hole
    (:method (close-hole ?from ?to) ;; opens a hole in the street
	   normal
	   ((backhoe ?backhoe))
	   ((get-to ?backhoe ?from)
	    (!fill-in ?backhoe ?from)))
    """
    if tasknames == ('GET-TO','!FILL-IN'):
        fromloc = params[0][2]
        if fromloc == params[1][2]:
            for toloc in poslocs:
                g.add((states[0],'CLOSE-HOLE', (fromloc, toloc)))
    # Missing get-to
    if tasknames == ('!FILL-IN',):
        fromloc = params[0][2]
        for toloc in poslocs:
            g.add((states[0],'CLOSE-HOLE', (fromloc, toloc)))
    """
    ;; set-up-cones
    (:method (set-up-cones ?from ?to) ;; sets up orange cones at road
	   normal
	   ((work-crew ?crew))
	   ((get-to ?crew ?from) (!place-cones ?crew)))
    """
    if tasknames == ('GET-TO','!PLACE-CONES'):
        fromloc = params[0][2]
        for toloc in poslocs:
            g.add((states[0],'SET-UP-CONES', (fromloc, toloc)))
    # Missing get-to
    if tasknames == ('!PLACE-CONES',):
        crew = params[0][1]
        m = unify(states[0][1], ('ATLOC', crew, None))
        # crew could be at both a town and posloc within a town
        if len(m)==1:
            fromloc = m.pop()[0]
            for toloc in poslocs:
                g.add((states[0],'SET-UP-CONES', (fromloc, toloc)))
        else:
            for fromloc in poslocs:
                for toloc in poslocs:
                    g.add((states[0],'SET-UP-CONES', (fromloc, toloc)))
    """
    ;; take-down-cones
    (:method (take-down-cones ?from ?to) ;; takes down cones
	   normal
	   ((work-crew ?crew))
	   ((get-to ?crew ?from) (!pickup-cones ?crew)))
    """
    if tasknames == ('GET-TO','!PICKUP-CONES'):
        fromloc = params[0][2]
        for toloc in poslocs:
            g.add((states[0],'TAKE-DOWN-CONES', (fromloc, toloc)))
    # Missing get-to
    if tasknames == ('!PICKUP-CONES',):
        crew = params[0][1]
        m = unify(states[0][1], ('ATLOC', crew, None))
        # crew could be at both a town and posloc within a town
        if len(m)==1:
            fromloc = m.pop()[0]
            for toloc in poslocs:
                g.add((states[0],'TAKE-DOWN-CONES', (fromloc, toloc)))
        else:
            for fromloc in poslocs:
                for toloc in poslocs:
                    g.add((states[0],'TAKE-DOWN-CONES', (fromloc, toloc)))
    """
    ;; clear-wreck
    (:method (clear-wreck ?from ?to) ;; gets rid of a wreck in any loc
	   normal
	   ((wrecked-vehicle ?from ?to ?veh) (garbage-dump ?dump))
	   ((tow-to ?veh ?dump)))
    """
    if tasknames == ('TOW-TO',):
        m = unify(states[0][1], ('WRECKED-VEHICLE', None, None, None))
        for (fromloc, toloc, veh) in m:
            g.add((states[0],'CLEAR-WRECK', (fromloc, toloc)))
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
    if tasknames == ('GET-TO','!HOOK-TO-TOW-TRUCK','GET-TO','!UNHOOK-FROM-TOW-TRUCK'):
        veh, toloc = params[1][2], params[2][2]
        g.add((states[0],'TOW-TO', (veh, toloc)))
    # Missing get-to branches
    if tasknames == ('!HOOK-TO-TOW-TRUCK','GET-TO','!UNHOOK-FROM-TOW-TRUCK'):
        veh, toloc = params[0][2], params[1][2]
        g.add((states[0],'TOW-TO', (veh, toloc)))
    if tasknames == ('GET-TO','!HOOK-TO-TOW-TRUCK','!UNHOOK-FROM-TOW-TRUCK'):
        veh = params[1][2]
        for toloc in ['BRIGHTON-DUMP','HENRIETTA-DUMP']:
            g.add((states[0],'TOW-TO', (veh, toloc)))
    if tasknames == ('!HOOK-TO-TOW-TRUCK','!UNHOOK-FROM-TOW-TRUCK'):
        veh = params[0][2]
        for toloc in ['BRIGHTON-DUMP','HENRIETTA-DUMP']:
            g.add((states[0],'TOW-TO', (veh, toloc)))
    """
    ;; clear-tree
    (:method (clear-tree ?tree) ;; this gets rid of a tree in any loc
	   normal
	   ((tree-crew ?tcrew) (tree ?tree) 
	    (atloc ?tree ?treeloc))
	   ((get-to ?tcrew ?treeloc) (!cut-tree ?tcrew ?tree)
	    (remove-blockage ?tree)))
    """
    if tasknames == ('GET-TO','!CUT-TREE','REMOVE-BLOCKAGE'):
        tree = params[1][2]
        g.add((states[0],'CLEAR-TREE', (tree,)))
    # Missing get-to
    if tasknames == ('GET-TO','!CUT-TREE'):
        tree = params[1][2]
        g.add((states[0],'CLEAR-TREE', (tree,)))
    if tasknames == ('!CUT-TREE','REMOVE-BLOCKAGE'):
        tree = params[0][2]
        g.add((states[0],'CLEAR-TREE', (tree,)))
    if tasknames == ('!CUT-TREE'):
        tree = params[0][2]
        g.add((states[0],'CLEAR-TREE', (tree,)))
    """
    ;; remove-blockage
    (:method (remove-blockage ?stuff)
	   move-to-side-of-street
	   ((work-crew ?crew) (atloc ?stuff ?loc))
	   ((get-to ?crew ?loc)
	    (!carry-blockage-out-of-way ?crew ?stuff)))
    """
    if tasknames == ('GET-TO','!CARRY-BLOCKAGE-OUT-OF-WAY'):
        stuff = params[1][2]
        g.add((states[0],'REMOVE-BLOCKAGE', (stuff,)))
    # Missing get-to
    if tasknames == ('!CARRY-BLOCKAGE-OUT-OF-WAY',):
        stuff = params[0][2]
        g.add((states[0],'REMOVE-BLOCKAGE', (stuff,)))
    """
    (:method (remove-blockage ?stuff)
	   carry-away
	   ((garbage-dump ?dump))
	   ((get-to ?stuff ?dump)))
    """
    if tasknames == ('GET-TO',):
        dump = params[0][2]
        if dump in ('HENRIETTA-DUMP','BRIGHTON-DUMP'):
            stuff = params[0][1]
            g.add((states[0],'REMOVE-BLOCKAGE', (stuff,)))
    """
    ;; declare-curfew
    (:method (declare-curfew ?town)
	   normal
	   ()
	   (:unordered (!call EBS) (!call police-chief)))
    """
    if tasknames == ('!CALL', '!CALL'):
        if 'EBS' in (params[0][1], params[1][1]):
            for town in locs:
                g.add((states[0],'DECLARE-CURFEW', (town,)))
    """
    ;; generate-temp-electricity
    (:method (generate-temp-electricity ?loc)
	   with-generator
	   ((generator ?gen))
	   ((make-full-fuel ?gen) (get-to ?gen ?loc) (!hook-up ?gen ?loc)
	    (!turn-on ?gen)))
    """
    if tasknames == ('MAKE-FULL-FUEL','GET-TO','!HOOK-UP','!TURN-ON'):
        loc = params[1][2]
        if loc == params[2][2]:
            g.add((states[0],'GENERATE-TEMP-ELECTRICITY', (loc,)))
    # Missing get-to
    if tasknames == ('MAKE-FULL-FUEL','!HOOK-UP','!TURN-ON'):
        loc = params[1][2]
        g.add((states[0],'GENERATE-TEMP-ELECTRICITY', (loc,)))
    """
    ;; make-full-fuel - makes sure arg1 is full of fuel
    (:method (make-full-fuel ?gen)
	   with-gas-can
	   ((gas-can ?gc) (atloc ?gen ?genloc) (service-station ?ss))
	   ((get-to ?gc ?ss) (add-fuel ?ss ?gc) (get-to ?gc ?genloc)
	    (!pour-into ?gc ?gen)))
    """
    if tasknames == ('GET-TO','ADD-FUEL','GET-TO','!POUR-INTO'):
        gen = params[3][2]
        if params[0][1] == params[1][2] == params[2][1]:
            g.add((states[0],'MAKE-FULL-FUEL', (gen,)))
    """
    (:method (make-full-fuel ?gen)
	   at-service-station
	   ((service-station ?ss))
	   ((get-to ?gen ?ss) (add-fuel ?ss ?gen)))
    """
    if tasknames == ('GET-TO','ADD-FUEL'):
        if params[0][1] == params[1][2] and params[0][2] == params[1][1]:
            gen = params[0][1]
            g.add((states[0],'MAKE-FULL-FUEL', (gen,)))
    # Missing get-to
    if tasknames == ('ADD-FUEL',):
        gen = params[0][2]
        g.add((states[0],'MAKE-FULL-FUEL', (gen,)))
    """
    ;; add-fuel (at service-station)
    (:method (add-fuel ?ss ?obj)
	   normal
	   ()
	   (:unordered (!pay ?ss) (!pump-gas-into ?ss ?obj)))
    """
    if tasknames in (('!PAY','!PUMP-GAS-INTO'), ('!PUMP-GAS-INTO','!PAY')):
        ss = params[0][1]
        if len(params[0]) > 2:
            obj = params[0][2]
        else:
            obj = params[1][2]
        g.add((states[0],'ADD-FUEL', (ss, obj)))
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
    """
    if tasknames in (('SHUT-OFF-POWER','CLEAR-TREE','!REMOVE-WIRE','!STRING-WIRE','TURN-ON-POWER'),('SHUT-OFF-POWER','!REMOVE-WIRE','CLEAR-TREE','!STRING-WIRE','TURN-ON-POWER')):
        crew, lineloc = params[0][1], params[0][2]
        g.add((states[0],'REPAIR-LINE', (crew, lineloc)))
    """
	   without-tree
	   ((atloc ?crew ?lineloc))
	   ((shut-off-power ?crew ?lineloc) 
	    (!remove-wire ?crew ?lineloc)
	    (!string-wire ?crew ?lineloc) (turn-on-power ?crew ?lineloc)))
    """
    if tasknames == ('SHUT-OFF-POWER','!REMOVE-WIRE','!STRING-WIRE','TURN-ON-POWER'):
        crew, lineloc = params[0][1], params[0][2]
        g.add((states[0],'REPAIR-LINE', (crew, lineloc)))
    """
    ;; shut-off-power
    (:method (shut-off-power ?crew ?loc)
	   normal
	   ((in-town ?loc ?town) (powerco-of ?town ?powerco))
	   (!call ?powerco))
    """
    if tasknames == ('!CALL',) and params[0][1] in powercos:
        for obj in states[0][0]:
            if obj in pcrews:
                for loc in powercos[params[0][1]]:
                    g.add((states[0],'SHUT-OFF-POWER', (obj, loc)))
    """
    ;; turn-on-power
    (:method (turn-on-power ?crew ?loc)
	   normal
	   ((in-town ?loc ?town) (powerco-of ?town ?powerco))
	   (!call ?powerco))
    """
    if tasknames == ('!CALL',) and params[0][1] in powercos:
        for obj in states[0][0]:
            if obj in pcrews:
                for loc in powercos[params[0][1]]:
                    g.add((states[0],'TURN-ON-POWER', (obj, loc)))
    """
    ;; shut-off-water
    (:method (shut-off-water ?from ?to)
	   normal
	   ((in-town ?from ?town) (waterco-of ?town ?waterco))
	   ((!call ?waterco)))
    """
    if tasknames == ('!CALL',) and params[0][1] in watercos:
        for fromloc in watercos[params[0][1]]:
            for toloc in poslocs:
                g.add((states[0],'SHUT-OFF-WATER', (fromloc, toloc)))
    """
    ;; turn-on-water
    (:method (turn-on-water ?from ?to)
	   normal
	   ((in-town ?from ?town) (waterco-of ?town ?waterco))
	   ((!call ?waterco)))
    """
    if tasknames == ('!CALL',) and params[0][1] in watercos:
        for fromloc in watercos[params[0][1]]:
            for toloc in poslocs:
                g.add((states[0],'TURN-ON-WATER', (fromloc, toloc)))
    """
    ;; emt-treat
    (:method (emt-treat ?person)
	   emt
	   ((emt-crew ?emt) (atloc ?person ?personloc))
	   ((get-to ?emt ?personloc) (!treat ?emt ?person)))
    """
    if tasknames == ('GET-TO', '!TREAT'):
        person = params[1][2]
        g.add((states[0],'EMT-TREAT', (person,)))
    # Missing get-to:
    if tasknames == ('!TREAT',):
        person = params[0][2]
        g.add((states[0],'EMT-TREAT', (person,)))
    """
    ;; stabilize
    (:method (stabilize ?person)
	   emt
	   ()
	   ((emt-treat ?person)))
    """
    if tasknames == ('EMT-TREAT',):
        person = params[0][1]
        g.add((states[0],'STABILIZE', (person,)))
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
    """
    if tasknames == ('DRIVE-TO',):
        person, place = params[0][1], params[0][3]
        g.add((states[0],'GET-TO', (person, place)))
    """
    (:method (get-to ?veh ?place)
	   vehicle-gets-driven
	   ((not (atloc ?veh ?place))
	    (person ?person)
	    (vehicle ?veh) (atloc ?veh ?vehloc)
	    (atloc ?person ?vehloc)
	    )
	   ((drive-to ?person ?veh ?place)))
    """
    if tasknames == ('DRIVE-TO',):
        veh, place = params[0][2], params[0][3]
        g.add((states[0],'GET-TO', (veh, place)))
    """
    (:method (get-to ?obj ?place)
	   as-cargo
	   ((not (atloc ?obj ?place))
	   (vehicle ?veh)
	   (atloc ?obj ?objloc)  (fit-in ?obj ?veh)
	   (not (non-ambulatory ?obj)))
	   ((get-to ?veh ?objloc) (get-in ?obj ?veh) (get-to ?veh ?place)
	    (get-out ?obj ?veh))
    """
    if tasknames == ('GET-TO','GET-IN','GET-TO','GET-OUT'):
        veh, obj, place = params[0][1], params[1][1], params[2][2]
        if (veh == params[1][2] == params[2][1] == params[3][2]) and (obj == params[3][1]):
            g.add((states[0],'GET-TO', (obj, place)))
            if obj[:3]=='GEN': # deal with monroe bug?
                g.add((states[0],'GET-TO', (obj, 'TEXACO1')))
    # Missing get-to
    if tasknames == ('GET-IN','GET-TO','GET-OUT'):
        veh, obj, place = params[0][2], params[0][1], params[1][2]
        if (veh == params[0][2] == params[1][1] == params[2][2]) and (obj == params[2][1]):
            g.add((states[0],'GET-TO', (obj, place)))
            if obj[:3]=='GEN': # monroe bug?
                g.add((states[0],'GET-TO', (obj, 'TEXACO1')))
    if tasknames == ('GET-TO','GET-IN','GET-OUT'):
        veh, obj = params[1][2], params[1][1]
        if (veh == params[0][1] == params[2][2]) and (obj == params[2][1]):
            m = unify(states[2][1], ('ATLOC', veh, None))
            if len(m)==1:
                place = m.pop()[0]
                g.add((states[0],'GET-TO', (obj, place)))
            else:
                for loc in poslocs:
                    g.add((states[0],'GET-TO',(obj,loc)))
            if obj[:3]=='GEN': # monroe bug?
                g.add((states[0],'GET-TO', (obj, 'TEXACO1')))
    if tasknames == ('GET-IN','GET-OUT'):
        veh, obj = params[1][2], params[1][1]
        if (veh == params[0][2]) and (obj == params[0][1]):
            m = unify(states[1][1], ('ATLOC', veh, None))
            if len(m)==1:
                place = m.pop()[0]
                g.add((states[0],'GET-TO', (obj, place)))
            else:
                m = unify(states[1][1], ('ATLOC', obj, None))
                if len(m)==1:
                    place  = m.pop()[0]
                    g.add((states[0],'GET-TO', (obj, place)))
                else:
                    for loc in poslocs:
                        g.add((states[0],'GET-TO',(obj,loc)))
            if obj[:3]=='GEN': # monroe bug?
                g.add((states[0],'GET-TO', (obj, 'TEXACO1')))
    """
	   with-ambulance ;; same as above, just with ambulance
	   ((not (atloc ?obj ?place))
	    (atloc ?obj ?objloc) (ambulance ?veh) (fit-in ?obj ?veh)
	    )
	   ((get-to ?veh ?objloc) (stabilize ?obj) (get-in ?obj ?veh)
	    (get-to ?veh ?place) (get-out ?obj ?veh))
	   )
    """
    if tasknames == ('GET-TO','STABILIZE','GET-IN','GET-TO','GET-OUT'):
        veh, obj, place = params[0][1], params[1][1], params[3][2]
        if (veh == params[2][2] == params[3][1] == params[4][2]) and (obj == params[2][1] == params[4][1]):
            g.add((states[0],'GET-TO', (obj, place)))
    # Missing get-to
    if tasknames == ('STABILIZE','GET-IN','GET-TO','GET-OUT'):
        veh, obj, place = params[1][2], params[0][1], params[2][2]
        if (veh == params[2][1] == params[3][2]) and (obj == params[1][1] == params[3][1]):
            g.add((states[0],'GET-TO', (obj, place)))
    """
    (:method (drive-to ?person ?veh ?loc)
	   normal
	   ((person ?person) (vehicle ?veh) (atloc ?veh ?vehloc)
	    (atloc ?person ?vehloc) (can-drive ?person ?veh))
	   ((!navegate-vehicle ?person ?veh ?loc)))
    """
    if tasknames == ('!NAVEGATE-VEHICLE',):
        person, veh, loc = params[0][1], params[0][2], params[0][3]
        g.add((states[0],'DRIVE-TO', (person, veh, loc)))
    """
    (:method (get-in ?obj ?veh)
	   ambulatory-person
	   ((atloc ?obj ?objloc) (atloc ?veh ?objloc) 
	    (person ?obj) (not (non-ambulatory ?obj)))
	   (!climb-in ?obj ?veh)
    """
    if tasknames == ('!CLIMB-IN',):
        obj, veh = params[0][1], params[0][2]
        g.add((states[0],'GET-IN', (obj, veh)))
    """
	   load-in
	   ((atloc ?obj ?objloc) (atloc ?veh ?objloc)
	    (person ?person) (can-lift ?person ?obj))
	   ((get-to ?person ?objloc) (!load ?person ?obj ?veh)))
    """
    if tasknames == ('GET-TO', '!LOAD'):
        obj, veh = params[1][2], params[1][3]
        g.add((states[0],'GET-IN', (obj, veh)))
    # Missing get-to
    if tasknames == ('!LOAD',):
        obj, veh = params[0][2], params[0][3]
        g.add((states[0],'GET-IN', (obj, veh)))
    """
    (:method (get-out ?obj ?veh)
	   ambulatory-person
	   ((person ?obj) (not (non-ambulatory ?obj)))
	   (!climb-out ?obj ?veh)
    """
    if tasknames == ('!CLIMB-OUT',):
        obj, veh = params[0][1], params[0][2]
        g.add((states[0],'GET-OUT', (obj, veh)))
    """
	   unload
	   ((atloc ?veh ?vehloc) (person ?person) (can-lift ?person ?obj))
	   ((get-to ?person ?vehloc) (!unload ?person ?obj ?veh)))
    """
    if tasknames == ('GET-TO', '!UNLOAD'):
        obj, veh = params[1][2], params[1][3]
        g.add((states[0],'GET-OUT', (obj, veh)))
    # Missing get-to
    if tasknames == ('!UNLOAD',):
        obj, veh = params[0][2], params[0][3]
        g.add((states[0],'GET-OUT', (obj, veh)))
    return g

def top_causes(v):
    """
    Encodes all top-level causal relations in the knowledge base.
    Inputs:
        v: A sequence of tasks in the form (state, taskname, parameters)
            Each state has the form (objects, facts)
    Outputs:
        g: The set of all possible causes of v, each also in the form (state, taskname, parameters).
    """
    states = tuple(s for (s,t,x) in v) # states (each of the form (objs, facts))
    tasknames = tuple(t for (s,t,x) in v)
    params = tuple((None,)+x for (s,t,x) in v) # Leading None for task name offset
    g = set()
    """
    ;;set-up-shelter sets up a shelter at a certain location
    (:method (set-up-shelter ?loc)
	   normal
	   ((shelter-leader ?leader)
	    (not (assigned-to-shelter ?leader ?other-shelter))
	    (food ?food))
	   ((get-electricity ?loc) (get-to ?leader ?loc) (get-to ?food ?loc)))
    """
    if tasknames == ('GET-ELECTRICITY','GET-TO','GET-TO'):
        loc = params[0][1]
        if loc == params[1][2] == params[2][2]:
            if params[1][1] in sleaders and params[2][1] in food:
                g.add((states[0],'SET-UP-SHELTER', (loc,)))
    # Missing get-elecricity
    if tasknames == ('GET-TO','GET-TO'):
        loc = params[0][2]
        if loc == params[1][2]:
            if params[0][1] in sleaders and params[1][1] in food:
                g.add((states[0],'SET-UP-SHELTER', (loc,)))
    """
    ;;fix-water-main
    (:method (fix-water-main ?from ?to)
	   normal
	   ()
	   ((shut-off-water ?from ?to) 
	    (repair-pipe ?from ?to)
	    (turn-on-water ?from ?to)))
    """
    if tasknames == ('SHUT-OFF-WATER','REPAIR-PIPE','TURN-ON-WATER'):
        fromloc, toloc = params[0][1], params[0][2]
        if (fromloc == params[1][1] == params[2][1]) and (toloc == params[1][2] == params[2][2]):
            g.add((states[0],'FIX-WATER-MAIN', (fromloc, toloc)))
    """
    ;; clear-road-hazard - cleans up a hazardous spill
    (:method (clear-road-hazard ?from ?to)
	   normal
	   ()
	   ((block-road ?from ?to)
	    (clean-up-hazard ?from ?to)
	    (unblock-road ?from ?to)))
    """
    if tasknames == ('BLOCK-ROAD','CLEAN-UP-HAZARD','UNBLOCK-ROAD'):
        fromloc, toloc = params[0][1], params[0][2]
        if (fromloc == params[1][1] == params[2][1]) and (toloc == params[1][2] == params[2][2]):
            g.add((states[0],'CLEAR-ROAD-HAZARD',(fromloc,toloc)))
    """
    ;; clear-road-wreck - gets a wreck out of the road
    (:method (clear-road-wreck ?from ?to)
	   normal
	   ()
	   ((set-up-cones ?from ?to)
	    (clear-wreck ?from ?to)
	    (take-down-cones ?from ?to)))
    """
    if tasknames == ('SET-UP-CONES','CLEAR-WRECK','TAKE-DOWN-CONES'):
        fromloc, toloc = params[0][1], params[0][2]
        if (fromloc == params[1][1] == params[2][1]) and (toloc == params[1][2] == params[2][2]):
            g.add((states[0],'CLEAR-ROAD-WRECK', (fromloc, toloc)))
    """
    ;; clear-road-tree
    (:method (clear-road-tree ?from ?to) ;; clears a tree that's in the road
	   normal
	   ((tree-blocking-road ?from ?to ?tree))
	   ((set-up-cones ?from ?to)
	    (clear-tree ?tree)
	    (take-down-cones ?from ?to)))
    """
    if tasknames == ('SET-UP-CONES','CLEAR-TREE','TAKE-DOWN-CONES'):
        fromloc, toloc = params[0][1], params[0][2]
        if (fromloc == params[2][1]) and (toloc == params[2][2]):
            g.add((states[0],'CLEAR-ROAD-TREE', (fromloc, toloc)))
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
    if tasknames == ('GET-TO','!NAVEGATE-SNOWPLOW','!ENGAGE-PLOW','!NAVEGATE-SNOWPLOW','!DISENGAGE-PLOW'):
        fromloc, toloc = params[1][3], params[3][3]
        if params[0][1] == params[1][1] == params[2][1] == params[3][1] == params[4][1]:
            g.add((states[0],'PLOW-ROAD',(fromloc,toloc)))
    # Missing get-to:
    if tasknames == ('!NAVEGATE-SNOWPLOW','!ENGAGE-PLOW','!NAVEGATE-SNOWPLOW','!DISENGAGE-PLOW'):
        fromloc, toloc = params[0][3], params[2][3]
        if params[0][1] == params[1][1] == params[2][1] == params[3][1]:
            g.add((states[0],'PLOW-ROAD',(fromloc,toloc)))
    """
    ;;quell-riot
    (:method (quell-riot ?loc)
	   with-police
	   ((in-town ?loc ?town)
	    (police-unit ?p1) (police-unit ?p2) (not (equal ?p1 ?p2)))
	   ((declare-curfew ?town) (get-to ?p1 ?loc) (get-to ?p2 ?loc)
	    (!set-up-barricades ?p1) (!set-up-barricades ?p2)))
    """
    if tasknames == ('DECLARE-CURFEW','GET-TO','GET-TO','!SET-UP-BARRICADES','!SET-UP-BARRICADES'):
        loc = params[1][2]
        if loc == params[2][2]:
            g.add((states[0],'QUELL-RIOT',(loc,)))
    # Missing get-to
    if tasknames == ('DECLARE-CURFEW','GET-TO','!SET-UP-BARRICADES','!SET-UP-BARRICADES',):
        loc = params[1][2]
        g.add((states[0],'QUELL-RIOT',(loc,)))
    if tasknames == ('DECLARE-CURFEW','!SET-UP-BARRICADES','!SET-UP-BARRICADES',):
        p2 = params[2][1]
        m = unify(states[2][1], ('ATLOC', p2, None))
        if len(m) == 1:
            loc = m.pop()[0]
            g.add((states[0],'QUELL-RIOT',(loc,)))
        else:
            p1 = params[1][1]
            m = unify(states[1][1], ('ATLOC', p1, None))
            if len(m)==1:
                loc = m.pop()[0]
                g.add((states[0],'QUELL-RIOT',(loc,)))
            else:
                for loc in poslocs:
                    g.add((states[0],'QUELL-RIOT',(loc,)))
    """
    ;;provide-temp-heat
    (:method (provide-temp-heat ?person)
	   to-shelter
	   ((person ?person) (shelter ?shelter))
	   ((get-to ?person ?shelter)))
    """
    if tasknames == ('GET-TO',):
        person = params[0][1]
        if len(person) >= 6 and person[:6]=='PERSON':
            g.add((states[0],'PROVIDE-TEMP-HEAT',(person,)))
    """
    (:method (provide-temp-heat ?person)
	   local-electricity
	   ((person ?person) (atloc ?person ?ploc))
	   ((generate-temp-electricity ?ploc) (!turn-on-heat ?ploc)))
    """
    if tasknames == ('GENERATE-TEMP-ELECTRICITY','!TURN-ON-HEAT'):
        for obj in states[0][0]:
            if len(obj) >= 6 and obj[:6] == 'PERSON':
                g.add((states[0],'PROVIDE-TEMP-HEAT',(obj,)))
    """
    ;;fix-power-line
    (:method (fix-power-line ?lineloc)
	   normal
	   ((power-crew ?crew) (power-van ?van))
	   ((get-to ?crew ?lineloc) (get-to ?van ?lineloc)
	    (repair-line ?crew ?lineloc)))
    """
    if tasknames == ('GET-TO','GET-TO','REPAIR-LINE'):
        lineloc = params[2][2] # params[0][2] need not be lineloc, monroe bug?
        if lineloc == params[1][2] and params[0][1]==params[2][1]:
            if params[0][1] in pcrews:
                g.add((states[0],'FIX-POWER-LINE', (lineloc,)))
    # Missing get-to
    if tasknames in [('GET-TO','REPAIR-LINE'),('REPAIR-LINE',)]:
        lineloc = params[-1][2]
        if lineloc == params[0][2]:
            g.add((states[0],'FIX-POWER-LINE', (lineloc,)))
    """
    ;;provide-medical-attention
    (:method (provide-medical-attention ?person)
	   in-hospital
	   ((hospital ?hosp) (has-condition ?person ?cond)
	    (not (hospital-doesnt-treat ?hosp ?cond)))
	   ((get-to ?person ?hosp) (!treat-in-hospital ?person ?hosp)))
    """
    if tasknames == ('GET-TO','!TREAT-IN-HOSPITAL'):
        person = params[0][1]
        if (person == params[1][1]):
            g.add((states[0],'PROVIDE-MEDICAL-ATTENTION', (person,)))
    # Missing get-to
    if tasknames == ('!TREAT-IN-HOSPITAL',):
        person = params[0][1]
        g.add((states[0],'PROVIDE-MEDICAL-ATTENTION', (person,)))
    """
    (:method (provide-medical-attention ?person)
	   simple-on-site
	   ((has-condition ?person ?cond) (not (serious-condition ?cond)))
	   ((emt-treat ?person)))
    """
    if tasknames == ('EMT-TREAT',):
        person = params[0][1]
        g.add((states[0],'PROVIDE-MEDICAL-ATTENTION', (person,)))
    return g

def causes(v):
    """
    Full causal relation (both mid- and top-level)
    """
    return top_causes(v) | mid_causes(v)

def main():
    pass
  
if __name__ == "__main__":
    main()
