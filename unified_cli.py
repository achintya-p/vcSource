#!/usr/bin/env python3
"""
Simple CLI for Unified VC Sourcing Agent
"""
import asyncio
import argparse
import json
from datetime import datetime

from unified_vc_sourcing_agent import UnifiedVCSourcingAgent

async def main():
    parser = argparse.ArgumentParser(description="Unified VC Sourcing CLI")
    parser.add_argument("vc_firm", help="Name of the VC firm")
    parser.add_argument("--mode", choices=["startups", "talent", "comprehensive"], 
                       default="comprehensive", help="Analysis mode")
    parser.add_argument("--max-startups", type=int, default=20, 
                       help="Maximum startups to analyze")
    parser.add_argument("--max-talent", type=int, default=5, 
                       help="Maximum talent per portfolio company")
    parser.add_argument("--platforms", nargs="+", 
                       default=["linkedin", "crunchbase", "twitter"],
                       help="Platforms to search for talent")
    parser.add_argument("--find-websites", action="store_true",
                       help="Find and validate company websites")
    parser.add_argument("--output", help="Output file for results")
    
    args = parser.parse_args()
    
    agent = UnifiedVCSourcingAgent(use_mock_data=True)
    
    print(f"\n🎯 Unified VC Sourcing for {args.vc_firm}")
    if args.find_websites:
        print("🌐 Website enhancement enabled")
    print("=" * 60)
    
    try:
        if args.mode == "startups":
            print("🚀 Running Startup Sourcing...")
            results = await agent.source_startups_for_vc(
                vc_firm=args.vc_firm,
                max_startups=args.max_startups,
                find_websites=args.find_websites
            )
            
            # Get portfolio companies with website enhancement if requested
            if args.find_websites:
                portfolio_companies = await agent._get_portfolio_companies(args.vc_firm, find_websites=True)
                print(f"\n🌐 Portfolio Companies with Websites:")
                for company in portfolio_companies[:10]:  # Show first 10
                    website_info = f" - {company.website}" if company.website else " - No website found"
                    print(f"   • {company.name}{website_info}")
            
            print(f"\n📊 Results:")
            print(f"   Portfolio Companies: {len(results.portfolio_companies)}")
            print(f"   Startups Found: {len(results.results)}")
            print(f"   Processing Time: {results.processing_time:.2f}s")
            
            print(f"\n🚀 Top Startup Matches:")
            for i, result in enumerate(results.results[:10], 1):
                print(f"\n{'='*60}")
                print(f"{i}. {result['company_name']}")
                print(f"{'='*60}")
                
                # Company Information
                print(f"🏢 Company Details:")
                print(f"   Industry: {result.get('industry', 'Unknown')}")
                print(f"   Location: {result.get('location', 'Unknown')}")
                print(f"   Funding Stage: {result.get('funding_stage', 'Unknown')}")
                print(f"   🌐 Website: {result.get('website', 'Not found')}")
                
                # Product Description
                print(f"\n📋 Product Description:")
                print(f"   {result.get('product_description', 'No description available')}")
                
                # Founders Information
                print(f"\n👥 Founders:")
                for founder in result.get('founders', []):
                    print(f"   • {founder.get('name', 'Unknown')} - {founder.get('title', 'Unknown')}")
                    print(f"     Experience: {founder.get('experience', 'Not available')}")
                    print(f"     Education: {founder.get('education', 'Not available')}")
                    connections = founder.get('linkedin_connections', 0)
                    endorsements = founder.get('endorsements', 0)
                    print(f"     LinkedIn: {connections} connections, {endorsements} endorsements")
                
                # Fit Metrics
                print(f"\n📊 Fit Metrics:")
                metrics = result.get('fit_metrics', {})
                print(f"   Overall Score: {metrics.get('overall_score', 0):.1f}")
                print(f"   Fit Score: {metrics.get('fit_score', 0):.1f}")
                print(f"   Quality Score: {metrics.get('quality_score', 0):.1f}")
                print(f"   Portfolio Fit Score: {metrics.get('portfolio_fit_score', 0):.1f}")
                print(f"   Text Similarity: {metrics.get('text_similarity', 0):.1f}")
                print(f"   Industry Alignment: {metrics.get('industry_alignment', 0):.1f}")
                print(f"   Stage Alignment: {metrics.get('stage_alignment', 0):.1f}")
                print(f"   Geographic Alignment: {metrics.get('geographic_alignment', 0):.1f}")
                print(f"   Network Proximity: {metrics.get('network_proximity', 0):.1f}")
                
                # Portfolio Analysis
                print(f"\n🎯 Portfolio Analysis:")
                conflict_details = result.get('portfolio_conflict_details', {})
                if conflict_details.get('has_conflicts'):
                    conflict_companies = conflict_details.get('conflict_companies', [])
                    conflict_types = conflict_details.get('conflict_types', [])
                    severity = conflict_details.get('severity', 'unknown')
                    print(f"   ⚠️  Conflicts: {', '.join(conflict_companies) if conflict_companies else 'None'}")
                    print(f"   Conflict Types: {', '.join(conflict_types) if conflict_types else 'None'}")
                    print(f"   Severity: {severity}")
                else:
                    print(f"   ✅ No portfolio conflicts detected")
                
                fit_details = result['portfolio_fit_details']
                portfolio_fit_score = fit_details.get('portfolio_fit_score') or fit_details.get('score', 0)
                reasoning = fit_details.get('reasoning', ['No reasoning available'])
                print(f"   Portfolio Fit Score: {portfolio_fit_score:.1f}")
                print(f"   Reasoning: {', '.join(reasoning) if isinstance(reasoning, list) else reasoning}")
                
                # Pros and Cons
                if result.get('pros'):
                    print(f"\n✅ Pros:")
                    for pro in result['pros']:
                        print(f"   • {pro}")
                
                if result.get('cons'):
                    print(f"\n❌ Cons:")
                    for con in result['cons']:
                        print(f"   • {con}")
                
                # Recommendation
                print(f"\n🎯 Recommendation: {result.get('recommendation', 'No recommendation available')}")
                print(f"{'='*60}")
        
        elif args.mode == "talent":
            print("👥 Running Talent Sourcing...")
            results = await agent.source_talent_for_portfolio(
                vc_firm=args.vc_firm,
                max_talent_per_company=args.max_talent,
                platforms=args.platforms
            )
            
            print(f"\n📊 Results:")
            print(f"   Portfolio Companies: {len(results.portfolio_companies)}")
            print(f"   Talent Found: {len(results.results)}")
            print(f"   Processing Time: {results.processing_time:.2f}s")
            
            print(f"\n👥 Top Talent Matches:")
            for i, result in enumerate(results.results[:10], 1):
                print(f"\n{i}. {result.get('name', 'Unknown')} - {result.get('title', 'Unknown')}")
                print(f"   Company: {result.get('company', 'Unknown')}")
                print(f"   Platform: {result.get('platform', 'Unknown')}")
                print(f"   Match Score: {result.get('match_score', 0):.1f}")
                
                if result.get('pros'):
                    print(f"   ✅ Pros: {', '.join(result['pros'])}")
                if result.get('cons'):
                    print(f"   ❌ Cons: {', '.join(result['cons'])}")
        
        else:  # comprehensive
            print("🎯 Running Comprehensive Analysis...")
            results = await agent.comprehensive_vc_analysis(
                vc_firm=args.vc_firm,
                max_startups=args.max_startups,
                max_talent=args.max_talent,
                platforms=args.platforms
            )
            
            print(f"\n📊 Comprehensive Results:")
            print(f"   VC Firm: {results['vc_firm']}")
            print(f"   Startups Found: {results['startup_sourcing']['total_startups_found']}")
            print(f"   Talent Found: {results['talent_sourcing']['total_talent_found']}")
            
            print(f"\n🚀 Top Startup Matches:")
            for i, result in enumerate(results['startup_sourcing']['results'][:5], 1):
                website_info = f" - {result.get('website', '')}" if result.get('website') else ""
                company_name = result.get('company_name', result.get('startup_name', 'Unknown'))
                overall_score = result.get('overall_score', result.get('fit_metrics', {}).get('overall_score', 0))
                print(f"{i}. {company_name} - Score: {overall_score:.1f}{website_info}")
            
            print(f"\n👥 Top Talent Matches:")
            for i, result in enumerate(results['talent_sourcing']['results'][:5], 1):
                name = result.get('name', 'Unknown')
                title = result.get('title', 'Unknown')
                company = result.get('company', 'Unknown')
                print(f"{i}. {name} - {title} at {company}")
        
        # Save results if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n💾 Results saved to: {args.output}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 