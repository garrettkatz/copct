# co-pct
## **P**arsimonious **C**overing **T**heory with causal **C**haining and **O**rdering constraints

`copct` is an automated cause-effect reasoning library based on Parsimonious Covering Theory.  Given a compendium of background knowledge, `copct` can automatically explain a set of observations by inferring causes from their effects.  `copct` is specialized for problems involving causal chaining (*A* causes *B*, *B* causes *C*, *C* causes *D* ...) and ordered effects (*A* causes *B*, then *C*, then *D* ...).  When there is more than one valid explanation, `copct` will find all of them.

### Example

Define background knowledge for a toy problem, where the causes and effects are labeled 'a' through 'f':

```python
>>> def causes(v):
    	U = set() # collect all possible direct causes of v
    	if v == ('a','b'): U.add('c') # the sequence (a,b) can be caused by c
    	if v == ('a','b'): U.add('d') # or by d
	if v == ('b','a','b'): U.add('e') # the sequence (b,a,b) can be caused by e
	if v == ('d','e'): U.add('f') # the sequence (d,e) can be caused by f
	return U
>>> longest_effects = 3 # the longest direct effect sequence has three elements (b,a,b)
```

Find all explanations for an observed sequence:

```python
>>> observations = ('b','a','b','a','b','a','b')
>>> _, explanations, _ = copct.explain(causes, longest_effects, observations)
>>> for (explanation, _, _, _, _) in explanations: print(explanation)
```

Select the most *parsimonious* explanations according to some criterion

```python
>>> parsimonious_explanations, _ = copct.minCardinalityTLCovers(explanations)
>>> for (explanation, _, _, _, _) in parsimonious_explanations: print(explanation)
```