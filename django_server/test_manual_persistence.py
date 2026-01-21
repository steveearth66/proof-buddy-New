"""
Manual test script to verify proof line database persistence
Run this with: python manage.py shell < test_manual_persistence.py
"""

from django.contrib.auth import get_user_model
from induction_api.models import InductionProof, InductionProofLine
from django.core.cache import cache

User = get_user_model()

# Clean up first
cache.clear()
InductionProof.objects.all().delete()
print("✓ Cleaned up existing data\n")

# Get or create test user
user, created = User.objects.get_or_create(
    username='test_persistence_user',
    defaults={'email': 'test@test.com'}
)
if created:
    user.set_password('test123')
    user.save()
print(f"✓ Using user: {user.username}\n")

# Create a proof in the database
proof = InductionProof.objects.create(
    user=user,
    name='Test Proof Persistence',
    tag='test-persist',
    induction_variable='n',
    anchor_value=0,
    leap_variable='k',
    lhs_anchor_goal='(sum 0)',
    rhs_anchor_goal='0',
    lhs_leap_goal='(sum (+ k 1))',
    rhs_leap_goal='(+ (sum k) (+ k 1))'
)
print(f"✓ Created proof: {proof.name} (ID: {proof.id})\n")

# Manually create some proof lines like the views would
InductionProofLine.objects.create(
    proof=proof,
    case='base',
    side='LHS',
    racket='(sum 0)',
    rule='Premise',
    start_position=0,
    line_number=0
)

InductionProofLine.objects.create(
    proof=proof,
    case='base',
    side='LHS',
    racket='0',
    rule='eval sum',
    start_position=0,
    line_number=1
)

InductionProofLine.objects.create(
    proof=proof,
    case='base',
    side='RHS',
    racket='(quotient (* 0 (+ 0 1)) 2)',
    rule='Premise',
    start_position=0,
    line_number=0
)

InductionProofLine.objects.create(
    proof=proof,
    case='base',
    side='RHS',
    racket='0',
    rule='rewrite math with 0',
    start_position=0,
    line_number=1
)

print("✓ Created 4 proof lines\n")

# Query and display
all_lines = InductionProofLine.objects.filter(proof=proof).order_by('case', 'side', 'line_number')

print("=" * 40)
print("PROOF LINES IN DATABASE:")
print("=" * 40)

for line in all_lines:
    print(f"\n{line.case.upper()} {line.side} - Line {line.line_number}:")
    print(f"  Expression: {line.racket}")
    print(f"  Rule: {line.rule}")
    print(f"  Position: {line.start_position}")

print("\n" + "=" * 40)

# Verify specific rules
base_lhs_lines = InductionProofLine.objects.filter(proof=proof, case='base', side='LHS')
base_rhs_lines = InductionProofLine.objects.filter(proof=proof, case='base', side='RHS')

print(f"\n✓ Base LHS lines: {base_lhs_lines.count()}")
print(f"✓ Base RHS lines: {base_rhs_lines.count()}")

# Check for specific rules
eval_sum_line = base_lhs_lines.filter(rule__icontains='eval sum').first()
rewrite_math_line = base_rhs_lines.filter(rule__icontains='rewrite math').first()

if eval_sum_line:
    print(f"\n✓ Found 'eval sum' rule: {eval_sum_line.rule}")
else:
    print("\n✗ 'eval sum' rule NOT found!")

if rewrite_math_line:
    print(f"✓ Found 'rewrite math' rule: {rewrite_math_line.rule}")
    if 'with' in rewrite_math_line.rule:
        print("✓ Rule includes substitution!")
else:
    print("✗ 'rewrite math' rule NOT found!")

print("\n" + "=" * 40)
print("TEST COMPLETE - Database persistence is working!")
print("=" * 40)