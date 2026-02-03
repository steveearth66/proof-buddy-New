# List Induction Implementation Progress

## Requirements

### List Induction vs Int Induction Differences

**When inductionType === 'lists':**

1. **aval (Anchor Value)**: Should be a list (typically `null` or `'(1)`) instead of an int
2. **ivar naming**: Typically `L` instead of `n` (not enforced)
3. **lvar (Leap Variable)**: 
   - Typically named `M` or `K` (instead of `m` or `k`)
   - Created as generic with type `list` (not `int`)

### UP Induction (Currently Implementing)
- **IH Formation**: Replace all instances of L (ivar) with K (lvar) - same as int
- **Leap Goals**: Replace L with `(cons a K)` where:
  - `a` is a new generic of type `Any`
  - Must create this generic when starting proof

### DOWN Induction (Not Yet Implemented)
- **IH Formation**: Replace L with `(rest K)`
- **Leap Goals**: Replace L with `K` directly
- No need to create generic `a`

## Implementation Progress

### Completed
- [x] Enable Lists radio button (removed `disabled` attribute)
- [x] Add state `listDirection` defaulting to 'up'

### In Progress
- [ ] Update validation to accept list values for aval
- [ ] Modify leap goal generation for UP list induction
- [ ] Create generic `a` of type `Any` during proof start
- [ ] Update backend to handle list structure

### Testing Plan
1. Test with Lists selected, simple list goal like `(sum L)` = `(* L (+ L 1) (quotient 1 2))`
2. Verify aval accepts `null` or list notation like `'(1)`
3. Verify lvar gets created as generic with type `list`
4. Verify leap goals replace L with `(cons a K)`
5. Verify generic `a` of type `Any` is created

### To Do
- [ ] Add UI for UP/DOWN selection (for later)
- [ ] Implement DOWN induction variant
- [ ] Backend changes in `start_induction_proof`
- [ ] Backend changes in `set_current_proof` for list structure
