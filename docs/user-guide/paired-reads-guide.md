# Paired Reads Management Guide

## Overview

Galaksio provides comprehensive support for managing paired-end sequencing reads in Galaxy. This guide will help you understand how to detect, manage, and work with paired reads effectively.

## What are Paired Reads?

Paired-end sequencing generates two reads for each DNA fragment:
- **Forward read (R1)**: Read from one end of the fragment
- **Reverse read (R2)**: Read from the opposite end

These reads are complementary and provide higher quality data when analyzed together.

## Supported Platforms and Patterns

Galaksio supports paired reads from various sequencing platforms:

### Illumina
- `_R1.fastq` / `_R2.fastq`
- `_1.fastq` / `_2.fastq`
- `_forward.fastq` / `_reverse.fastq`

### Oxford Nanopore
- Single FASTQ files containing both reads
- Pattern-based detection for paired runs

### Generic Patterns
- `_read1.fastq` / `_read2.fastq`
- `_pair1.fastq` / `_pair2.fastq`

## Supported File Formats

- **FASTQ**: `.fastq`, `.fq`
- **FASTA**: `.fasta`, `.fa`, `.fas`
- **Compressed**: `.fastq.gz`, `.fq.gz`, `.fasta.gz`, `.fa.gz`, `.fas.gz`
- **Aligned**: `.bam`, `.sam`

## Using the Paired Reads Manager

### 1. Access the Paired Reads Manager

Navigate to the "Paired Reads" section in the Galaksio interface.

### 2. Select a Galaxy History

The paired reads manager works with the current Galaxy history. Make sure you have:
- Selected the correct history in Galaxy
- Uploaded your sequencing data to the history

### 3. Detect Paired Reads

Click the "Detect Paired Reads" button to analyze your history:

1. **Analysis Process**: Galaksio scans all datasets in your history
2. **Pattern Matching**: Uses intelligent algorithms to identify potential pairs
3. **Confidence Scoring**: Each potential pair receives a confidence score (0.0-1.0)
4. **Results Display**: Shows detected pairs and unpaired reads

### 4. Understanding the Results

#### Detected Pairs Table
- **Forward/Reverse Read**: Names and IDs of the paired files
- **Platform**: Detected sequencing platform
- **Confidence**: Match confidence with visual indicator
- **Pattern**: The naming pattern that was matched

#### Confidence Levels
- **High (0.8-1.0)**: Very confident match
- **Medium (0.6-0.8)**: Likely match, manual review recommended
- **Low (0.0-0.6)**: Possible match, verification needed

#### Statistics Cards
- **Total Datasets**: All sequencing files in the history
- **Paired Datasets**: Files successfully paired
- **Unpaired Datasets**: Files without detected pairs
- **Pairing Rate**: Percentage of files that were paired

### 5. Working with Pairs

#### Selecting Pairs
- Use checkboxes to select individual pairs
- Use "Select High Confidence" to automatically select pairs with confidence ≥ threshold
- Use "Clear Selection" to deselect all pairs

#### Creating Collections
1. Select the pairs you want to group
2. Click "Create Collections"
3. Galaksio will create paired dataset collections in Galaxy

#### Auto-Pairing
1. Set your desired confidence threshold
2. Click "Auto Pair All"
3. Galaksio will automatically create collections for all high-confidence pairs

### 6. Managing Unpaired Reads

The "Unpaired Reads" section shows files that couldn't be paired:
- Review these files manually
- Check for naming inconsistencies
- Consider if they should remain unpaired (single-end data)

## Advanced Features

### Confidence Threshold Adjustment

Adjust the confidence threshold based on your needs:
- **Higher threshold (0.8+)**: More conservative, fewer false positives
- **Lower threshold (0.6+)**: More inclusive, may include some false positives

### Export Functionality

Export paired reads data for:
- Documentation purposes
- External analysis
- Sharing with collaborators

### Pair Details View

Click the eye icon to see detailed information about each pair:
- File metadata
- Confidence calculation details
- Platform-specific information

## Best Practices

### 1. File Naming Consistency
- Use consistent naming conventions
- Follow platform-specific naming patterns
- Avoid special characters in filenames

### 2. Quality Control
- Review low-confidence pairs manually
- Verify that paired files contain related data
- Check file sizes (paired files should be similar sizes)

### 3. Organization
- Create meaningful collection names
- Group related pairs together
- Document your pairing decisions

### 4. Performance Tips
- Work with manageable history sizes
- Use auto-pairing for large datasets
- Monitor system resources during processing

## Troubleshooting

### Common Issues

#### No Pairs Detected
- **Cause**: Files don't follow supported naming patterns
- **Solution**: Rename files to match supported patterns

#### Low Confidence Scores
- **Cause**: Unusual naming conventions or mixed platforms
- **Solution**: Manual review and verification

#### Missing Files
- **Cause**: Files not uploaded to Galaxy or wrong history selected
- **Solution**: Verify files are in the correct history

#### Collection Creation Fails
- **Cause**: Insufficient permissions or Galaxy API issues
- **Solution**: Check Galaxy connection and permissions

### Error Messages

#### "No history selected"
- Ensure you have a current history selected in Galaxy
- Refresh the Galaksio interface

#### "Failed to detect paired reads"
- Check your internet connection
- Verify Galaxy instance is accessible
- Try refreshing the page

#### "Collection creation failed"
- Verify you have write permissions in Galaxy
- Check that files are not already in collections
- Try creating collections manually in Galaxy

## API Integration

For programmatic access, Galaksio provides REST API endpoints:

### Detect Paired Reads
```bash
curl -X POST http://localhost:8081/api/detect_paired_reads \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"history_id": "YOUR_HISTORY_ID"}'
