import sys
import argparse
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.converter import SHACLToSouffleConverter
from src.performance_evaluator import PerformanceEvaluator

def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('shacl2datalog.log')
        ]
    )

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='SHACL to Datalog Converter',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-o', '--output', default='output', help='Output directory')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert SHACL to Datalog')
    convert_parser.add_argument('shacl_file', help='SHACL file path')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate with data')
    validate_parser.add_argument('shacl_file', help='SHACL file path')
    validate_parser.add_argument('--data', help='Data file or directory')
    validate_parser.add_argument('--wikidata', action='store_true', help='Use Wikidata')
    validate_parser.add_argument('--entity-type', default='person', help='Entity type for Wikidata')
    validate_parser.add_argument('--sample-size', type=int, default=1000, help='Sample size')
    
    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare with pySHACL')
    compare_parser.add_argument('shacl_file', help='SHACL file path')
    compare_parser.add_argument('data_file', help='Data file path')
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    if not args.command:
        parser.print_help()
        return
    
    converter = SHACLToSouffleConverter()
    
    try:
        if args.command == 'convert':
            result = converter.convert_file(args.shacl_file, args.output)
            if result['success']:
                print(f"✅ Conversion successful!")
                print(f"📁 Output: {result['program_file']}")
                print(f"📊 Shapes: {result['parser_stats']['shapes_count']}")
                print(f"📊 Rules: {result['generator_stats']['rules_count']}")
            else:
                print(f"❌ Conversion failed: {result.get('error', 'Unknown error')}")
                
        elif args.command == 'validate':
            if args.wikidata:
                result = converter.validate_with_wikidata(
                    args.shacl_file,
                    entity_type=args.entity_type,
                    sample_size=args.sample_size,
                    output_dir=args.output
                )
            else:
                # Implement custom data validation
                print("Custom data validation not yet implemented")
                return
            
            if result.get('success'):
                print(f"✅ Validation complete!")
                print(f"📊 Performance: {result.get('performance', {})}")
            else:
                print(f"❌ Validation failed")
                
        elif args.command == 'compare':
            # Run comparison
            evaluator = PerformanceEvaluator(args.output)
            
            # Convert SHACL
            conversion = converter.convert_file(args.shacl_file, args.output)
            
            # Prepare test case
            test_case = {
                'name': Path(args.shacl_file).stem,
                'shacl_file': args.shacl_file,
                'data_file': args.data_file,
                'souffle_program': conversion['program'],
                'facts_dir': Path(args.data_file).parent,
                'data_size': 1000  # You'd calculate this from the data
            }
            
            # Compare systems
            df = evaluator.compare_systems([test_case])
            report = evaluator.generate_report(df)
            
            print("📊 Comparison complete!")
            print(report)
            
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

